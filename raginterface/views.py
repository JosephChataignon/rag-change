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
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.exception(f"Chat API error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_POST  
def chat_stream_api(request):
    logger.info(f"Chat Stream API accessed with request: {request}")
    try:
        query = request.POST.get('query', '').strip()
        if not query:
            return JsonResponse({'error': 'Query is required'}, status=400)
        
        # Test LLM service availability
        if not isinstance(llm_service.test(), str):
            logger.error("Error: LLM service is not available.")
            return JsonResponse({'error': 'LLM service is not available'}, status=500)
        
        n_results = config.get('n_results')
        
        def generate_stream_response(query, n_results):
            try:
                # Search for relevant documents
                search_data = vector_retriever.retrieve(query, n_results)
                # Construct prompt for LLM   
                prompt=search_data['formatted_data']
                chunk_count = 0
                for chunk in llm_service.stream_response(prompt):
                    yield chunk
                    chunk_count += 1
                    if chunk_count % 50 == 0: # Force garbage collection every 50 chunks
                        gc.collect()
                
                # After streaming is complete, send document metadata
                docs_json = json.dumps(search_data['documents'])
                yield f"<|DOCS_JSON|>{docs_json}"
                
            except Exception as e:
                logger.exception("Error during streaming response generation")
                yield f"\n\nError during response generation: {str(e)[:100]}..."
                yield f"<|DOCS_JSON|>{docs_json if 'docs_json' in locals() else '[]'}"
            finally:
                # Final cleanup
                gc.collect()
                
        def response_generator():
            for chunk in generate_stream_response(query, n_results):
                yield chunk
            
        response = StreamingHttpResponse(
            response_generator(),
            content_type='text/plain'
        )
        logger.info(f"Streaming response initiated: {response}")
        return response

    except Exception as e:
        logger.exception(f"Chat Stream API error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
