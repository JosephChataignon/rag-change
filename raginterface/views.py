import json, logging, gc
from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from ragchange.config.loader import config

from raginterface.models import ChatLog
from raginterface.services.llm import LLMService
from raginterface.services.vector_search import ChromaRetriever

logger = logging.getLogger('raginterface')
llm_service = LLMService()
vector_retriever = ChromaRetriever()

# Create your views here.
def home(request):
    logger.info(f"Home page accessed with request: {request}")
    return render(request, 'raginterface/home.html', context={'n_results':config.get('n_results')})

def search(request):
    logger.info(f"Search interface accessed with request: {request}")
    return render(request, 'raginterface/search.html', context={'n_results':config.get('n_results')})

def chat(request):
    logger.info(f"Chat interface accessed with request: {request}")
    return render(request, 'raginterface/chat.html')


def _get_chat_log(request):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    chat_log, _ = ChatLog.objects.get_or_create(session_key=session_key)
    chat_log.content.setdefault("turns", [])
    return chat_log


def _build_messages_from_transcript(chat_log, retrieval_results, query):
    system_prompt = config.get('rag_system_prompt')
    messages = [{"role": "system", "content": system_prompt}]

    for turn in chat_log.content.get("turns"):
        user_text = turn.get("query")
        assistant_text = turn.get("response")
        if user_text: messages.append({"role": "user", "content": user_text})
        if assistant_text: messages.append({"role": "assistant", "content": assistant_text})

    prompt_template = config.get('rag_prompt')
    prompt = prompt_template.format(data=retrieval_results, query=query)
    messages.append({"role": "user", "content": prompt})
    return messages


@require_POST  
def search_api(request):
    logger.info(f"Search API accessed with request: {request}")
    try:
        query = request.POST.get('query', '').strip()
        n_results = int(request.POST.get('number_results'))
        
        if not query or not n_results or n_results <= 0:
            return JsonResponse({'error': 'Requires query and n_results>0'}, status=400)
        
        logger.info(f"Processing search query: '{query}'")
        
        # Use the service to search documents
        search_data = vector_retriever.retrieve(query, n_results)
        
        # Format response for the frontend
        response_data = {
            'query': query,
            'documents': search_data['documents'],
            'total_results': len(search_data['documents']),
            'formatted_data': search_data['formatted_data']
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.exception("Search API error")
        return JsonResponse({'error': str(e)}, status=500)

@require_POST  
def chat_api(request):
    logger.info(f"Chat API accessed with request: {request}")
    try:
        # Parse JSON body for API requests
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            n_results = data.get('n_results')
        else:
            # Fallback to form data
            query = request.POST.get('query', '').strip()
            n_results = int(request.POST.get('n_results', config.get('n_results')))
        
        if not query or not n_results:
            return JsonResponse({'error': 'Requires query and n_result'}, status=400)
            
        logger.info(f"Processing chat query: '{query}'")
        chat_log = _get_chat_log(request)
        
        # vector search
        retrieval_results = vector_retriever.retrieve(query)
        # prompt construction
        messages = _build_messages_from_transcript(chat_log, retrieval_results, query)
        # call LLM service
        result = llm_service.generate_response(messages)

        chat_log.content["turns"].append({
            "query": query,
            "response": result,
            "llm_model": config.get('llm_model'),
            "embedding_model": config.get('embedding_model'),
            "vector_db": config.get('vector_db_path'),
            "n_results": n_results
        })
        
        with transaction.atomic():
            chat_log.save(update_fields=["content"])

        docs_json = json.dumps(retrieval_results.get('documents', []))
        response_text = f"{result}<|DOCS_JSON|>{docs_json}"
        return HttpResponse(response_text, content_type='text/plain')
        
    except Exception as e:
        logger.exception(f"Chat API error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

