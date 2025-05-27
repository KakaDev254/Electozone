from django.http import JsonResponse
from .ai import chat_with_bot

def chatbot_api(request):
    message = request.GET.get('message', '')
    if message:
        response = chat_with_bot(message)
    else:
        response = "Please type a message."
    return JsonResponse({'response': response})
