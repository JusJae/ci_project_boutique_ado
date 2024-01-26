from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """
    This class will be used to store static files on AWS
    """
    location = settings.STATICFILES_LOCATION


class MediaStorage(S3Boto3Storage):
    """
    This class will be used to store media files on AWS
    """
    location = settings.MEDIAFILES_LOCATION
