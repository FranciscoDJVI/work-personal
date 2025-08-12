"""
Custom exception handler for PsysMsql API

This module provides custom exception handling for better error responses
and logging in the API.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import Http404
import logging

logger = logging.getLogger('psysmysql.api')


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    and logs errors appropriately.
    """
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Get the view and request from context
    view = context.get('view', None)
    request = context.get('request', None)
    
    # Log the exception
    if response is not None:
        logger.warning(
            f"API Exception: {exc.__class__.__name__} - {str(exc)} - "
            f"View: {view.__class__.__name__ if view else 'Unknown'} - "
            f"User: {request.user if request and hasattr(request, 'user') else 'Anonymous'}"
        )
    else:
        logger.error(
            f"Unhandled API Exception: {exc.__class__.__name__} - {str(exc)} - "
            f"View: {view.__class__.__name__ if view else 'Unknown'} - "
            f"User: {request.user if request and hasattr(request, 'user') else 'Anonymous'}"
        )
    
    # Handle specific Django exceptions that DRF doesn't handle by default
    if response is None:
        
        if isinstance(exc, ValidationError):
            custom_response_data = {
                'error': 'Validation Error',
                'message': 'Los datos proporcionados no son válidos',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else [str(exc)],
                'code': 'validation_error'
            }
            response = Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(exc, IntegrityError):
            custom_response_data = {
                'error': 'Integrity Error',
                'message': 'Error de integridad en la base de datos. Posible duplicación o violación de restricción.',
                'details': str(exc),
                'code': 'integrity_error'
            }
            response = Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(exc, Http404):
            custom_response_data = {
                'error': 'Not Found',
                'message': 'El recurso solicitado no fue encontrado',
                'details': str(exc),
                'code': 'not_found'
            }
            response = Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)
            
        elif isinstance(exc, PermissionError):
            custom_response_data = {
                'error': 'Permission Denied',
                'message': 'No tienes permisos para realizar esta acción',
                'details': str(exc),
                'code': 'permission_denied'
            }
            response = Response(custom_response_data, status=status.HTTP_403_FORBIDDEN)
    
    # Customize response format for consistency
    if response is not None:
        if hasattr(response, 'data'):
            # Ensure consistent error response format
            if isinstance(response.data, dict):
                # If it's already our custom format, leave it as is
                if 'error' not in response.data:
                    custom_data = format_error_response(response.data, response.status_code)
                    response.data = custom_data
            elif isinstance(response.data, list):
                # Handle list of errors (like validation errors)
                custom_data = {
                    'error': get_error_type_from_status(response.status_code),
                    'message': get_error_message_from_status(response.status_code),
                    'details': response.data,
                    'code': get_error_code_from_status(response.status_code)
                }
                response.data = custom_data
    
    return response


def format_error_response(data, status_code):
    """
    Format error response to ensure consistency
    """
    if isinstance(data, dict):
        # Check if it's already formatted
        if 'error' in data:
            return data
        
        # Format DRF validation errors
        if 'detail' in data:
            return {
                'error': get_error_type_from_status(status_code),
                'message': str(data['detail']),
                'details': data,
                'code': get_error_code_from_status(status_code)
            }
        
        # Format field validation errors
        formatted_details = {}
        for field, messages in data.items():
            if isinstance(messages, list):
                formatted_details[field] = messages
            else:
                formatted_details[field] = [str(messages)]
        
        return {
            'error': get_error_type_from_status(status_code),
            'message': get_error_message_from_status(status_code),
            'details': formatted_details,
            'code': get_error_code_from_status(status_code)
        }
    
    return {
        'error': get_error_type_from_status(status_code),
        'message': str(data) if data else get_error_message_from_status(status_code),
        'details': data,
        'code': get_error_code_from_status(status_code)
    }


def get_error_type_from_status(status_code):
    """Get error type based on HTTP status code"""
    error_types = {
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        406: 'Not Acceptable',
        409: 'Conflict',
        410: 'Gone',
        422: 'Unprocessable Entity',
        429: 'Too Many Requests',
        500: 'Internal Server Error',
        501: 'Not Implemented',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
    }
    return error_types.get(status_code, 'Error')


def get_error_message_from_status(status_code):
    """Get user-friendly error message based on HTTP status code"""
    messages = {
        400: 'La solicitud contiene datos inválidos',
        401: 'Credenciales de autenticación no proporcionadas o inválidas',
        403: 'No tienes permisos para realizar esta acción',
        404: 'El recurso solicitado no fue encontrado',
        405: 'Método HTTP no permitido para este endpoint',
        406: 'El formato solicitado no es aceptable',
        409: 'Conflicto con el estado actual del recurso',
        410: 'El recurso ya no está disponible',
        422: 'Los datos enviados no pueden ser procesados',
        429: 'Demasiadas solicitudes. Intenta nuevamente más tarde',
        500: 'Error interno del servidor',
        501: 'Funcionalidad no implementada',
        502: 'Error de gateway',
        503: 'Servicio no disponible temporalmente',
    }
    return messages.get(status_code, 'Ha ocurrido un error')


def get_error_code_from_status(status_code):
    """Get error code based on HTTP status code"""
    codes = {
        400: 'bad_request',
        401: 'unauthorized',
        403: 'forbidden',
        404: 'not_found',
        405: 'method_not_allowed',
        406: 'not_acceptable',
        409: 'conflict',
        410: 'gone',
        422: 'unprocessable_entity',
        429: 'too_many_requests',
        500: 'internal_server_error',
        501: 'not_implemented',
        502: 'bad_gateway',
        503: 'service_unavailable',
    }
    return codes.get(status_code, 'error')
