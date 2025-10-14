from core.models import ActivityLog

def log_activity(request, activity_type, description, details='', object_type='', object_id='', extra_data=None):
    """
    Helper function para registrar atividades facilmente nas views
    
    Usage:
    from core.activity_utils import log_activity
    log_activity(request, 'UPLOAD', 'Arquivo enviado', 'planilha.xlsx processada')
    """
    if request.user.is_authenticated:
        return ActivityLog.log_activity(
            user=request.user,
            activity_type=activity_type,
            description=description,
            details=details,
            object_type=object_type,
            object_id=object_id,
            request=request,
            extra_data=extra_data
        )
    return None

# Decorator para registrar atividades automaticamente
def log_activity_decorator(activity_type, description_template, object_type=''):
    """
    Decorator para registrar atividades automaticamente
    
    Usage:
    @log_activity_decorator('VIEW', 'Dashboard acessado')
    def dashboard_view(request):
        ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            
            if request.user.is_authenticated:
                # Formatear description se for um template
                description = description_template.format(
                    user=request.user.username,
                    **kwargs
                )
                
                log_activity(
                    request=request,
                    activity_type=activity_type,
                    description=description,
                    object_type=object_type
                )
            
            return response
        
        wrapper.__name__ = view_func.__name__
        wrapper.__doc__ = view_func.__doc__
        return wrapper
    
    return decorator