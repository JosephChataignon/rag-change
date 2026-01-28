import json, logging, gc
from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from ragchange.config.loader import config

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

@require_POST  
def search_api(request):
    logger.info(f"Search API accessed with request: {request}")
    try:
        query = request.POST.get('query', '').strip()
        n_results = int(request.POST.get('number_results'))
        
        if not query or not n_results or n_results <= 0:
            return JsonResponse({'error': 'Requires query and n_results>0'}, status=400)
        
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
        
        # vector search
        retrieval_results = vector_retriever.retrieve(query)
        # prompt construction
        prompt_template = config.get('rag_prompt')
        prompt = prompt_template.format(data=retrieval_results, query=query)
        # call LLM service
        result = llm_service.generate_response(prompt)
        docs_json = json.dumps(retrieval_results.get('documents', []))
        response_text = f"{result}<|DOCS_JSON|>{docs_json}"

        return HttpResponse(response_text, content_type='text/plain')
        
    except Exception as e:
        logger.exception(f"Chat API error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

