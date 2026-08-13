import json, logging, re, gc
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

def _format_results_for_prompt(retrieval_results):
    """Formats the retrieval results from a dict into a string, including some metadata."""
    formatted_data = f"Number of documents: {len(retrieval_results)}\n"
    for doc in retrieval_results:
        formatted_data += f"File Name: {doc['file_name']}\n"
        formatted_data += f"Content:\n{doc['content']}\n"
        formatted_data += "-" * 80 + "\n"

    return formatted_data

def _build_messages_from_transcript(chat_log, retrieval_results, query):
    system_prompt = config.get('rag_system_prompt')
    messages = [{"role": "system", "content": system_prompt}]

    for turn in chat_log.content.get("turns"):
        user_text = turn.get("query")
        assistant_text = turn.get("response")
        if user_text: messages.append({"role": "user", "content": user_text})
        if assistant_text: messages.append({"role": "assistant", "content": assistant_text})

    prompt_template = config.get('rag_prompt')
    formatted_results = _format_results_for_prompt(retrieval_results)
    prompt = prompt_template.format(data=formatted_results, query=query)
    messages.append({"role": "user", "content": prompt})
    return messages

def _augment_query(query):
    system_prompt = "You are a reformulation tool in a search engine. You will be given a user question and you will formulate search queries that will help find relevant information. The theme of the questions and documents is Education Science. Generated search queries should be varied, should use Education Science terminology, and should be relevant to the original question."
    query_prompt = f"Generate 3 search queries in English and 3 in German. Use the following json output format: \n {{ \"queries\": [\"query1\", \"query2\", \"query3\", \"query4\", \"query5\", \"query6\"] }} \n User original question: '{query}'"
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": query_prompt}]
    result = llm_service.generate_response(messages)
    try:
        m = re.search(r"\{[^}]*['\"]?queries['\"]?\s*:\s*\[.*?\][^}]*\}", result, re.S)
        queries = json.loads(m.group(0))['queries'] #TODO: force json formatting on LLM ?
    except (json.JSONDecodeError, AttributeError):
        logger.error(f"Failed to parse augmented queries from LLM response: {result}")
        raise ValueError("Failed to parse augmented queries from LLM response.")
    logger.info(f"Augmented query '{query}' into {queries}")
    return queries


@require_POST  
def search_api(request):
    logger.info(f"Search API accessed with request: {request}")
    try:
        query = request.POST.get('query', '').strip()
        n_results = int(request.POST.get('number_results'))
        
        if not query or not n_results or n_results <= 0:
            return JsonResponse({'error': 'Requires query and n_results>0'}, status=400)
        logger.info(f"Processing search query: '{query}'\n\tNumber of results requested: {n_results}")
        
        query_augmentation = False #TODO: when to turn it on ?
        # Use the service to search documents
        queries = _augment_query(query) if query_augmentation else [query]
        retrieval_results = vector_retriever.retrieve(queries, n_results)
        
        # Format response for the frontend
        response_data = {
            'query': query,
            'documents': retrieval_results
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
        logger.info(f"Processing chat query: '{query}'\n\tNumber of results requested: {n_results}")
        
        chat_log = _get_chat_log(request)
        
        # vector search
        queries = _augment_query(query)
        search_data = vector_retriever.retrieve(queries, n_results)
        # prompt construction
        messages = _build_messages_from_transcript(chat_log, search_data, query)
        # call LLM service
        result = llm_service.generate_response(messages)

        # save chat
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

        # return response
        docs_json = json.dumps(search_data)
        response_text = f"{result}<|DOCS_JSON|>{docs_json}"
        return HttpResponse(response_text, content_type='text/plain')
        
    except Exception as e:
        logger.exception(f"Chat API error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

