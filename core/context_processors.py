from downloads.models import BookDownload

def user_downloads_count(request):
    if request.user.is_authenticated:
        return {
            'user_downloads_count': BookDownload.objects.filter(user=request.user).count()
        }
    return {'user_downloads_count': 0}