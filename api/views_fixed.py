@extend_schema(
    tags=['system'],
    operation_id='health',
    summary='System Health Status Check',
    description="""Health check endpoint that monitors system vitals, performance metrics, and server status"""
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """
    Comprehensive health check endpoint that monitors system vitals, performance
    metrics, and server status in both UTC and Shamsi (Iranian) time.
    """
    # Start time for response timing
    start_time = time.time()
    
    # Check database connection
    db_status = "connected"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Get system uptime
    uptime_seconds = time.time() - START_TIME
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"
    
    # Get server time in Shamsi (Iranian) calendar
    now = timezone.now()
    jnow = jdatetime.datetime.fromgregorian(datetime=now)
    shamsi_time = jnow.strftime('%Y/%m/%d %H:%M:%S')
    
    # Get system info (CPU, memory)
    detailed = request.query_params.get('detailed', 'false').lower() == 'true'
    
    # Basic response
    response_data = {
        'status': 'ok' if db_status == "connected" else 'error',
        'database': db_status,
        'version': '1.0.0',
        'uptime': uptime,
        'server_time': shamsi_time,
        'server_time_utc': now.isoformat(),
    }
    
    # Add system info if detailed view is requested
    if detailed:
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=0.5)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024 * 1024 * 1024)
            memory_available_gb = memory.available / (1024 * 1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024 * 1024 * 1024)
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Add system info to response
            response_data['system_info'] = {
                'cpu_usage': cpu_usage,
                'memory_usage': {
                    'total': f"{memory_total_gb:.2f}GB",
                    'available': f"{memory_available_gb:.2f}GB",
                    'percent': memory.percent
                },
                'disk_usage': {
                    'total': f"{disk_total_gb:.2f}GB",
                    'used': f"{disk_used_gb:.2f}GB",
                    'free': f"{disk_free_gb:.2f}GB",
                    'percent': disk.percent
                },
                'python_version': platform.python_version(),
                'django_version': django.__version__
            }
            
            # Add application config info if requested
            response_data['application_info'] = {
                'environment': 'development' if settings.DEBUG else 'production',
                'debug_mode': settings.DEBUG,
                'allowed_hosts': settings.ALLOWED_HOSTS,
                'database_engine': settings.DATABASES['default']['ENGINE'],
                'installed_apps': settings.INSTALLED_APPS
            }
            
            # Check cache
            cache_key = 'health_check_test'
            cache_value = 'test_value'
            cache.set(cache_key, cache_value, 10)
            cache_status = "working" if cache.get(cache_key) == cache_value else "error"
            response_data['cache_status'] = cache_status
            
        except Exception as e:
            response_data['system_info_error'] = str(e)
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Set response headers
    response = Response(response_data)
    response['X-Response-Time'] = f"{response_time:.3f} seconds"
    response['X-System-Status'] = 'healthy' if response_data['status'] == 'ok' else 'error'
    
    return response 