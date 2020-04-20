import os
import uuid
import datetime
from urllib.parse import urljoin

from django.conf import settings
from redactor.utils import import_class


class BaseUploaderRedactor(object):
    """
    Base class for uploader handler.
    """

    def __init__(self, upload_file, upload_to=None):
        self.upload_file = upload_file
        self.upload_to = upload_to

        file_storage_class = getattr(settings, 'REDACTOR_FILE_STORAGE',
                                     'django.core.files.storage.DefaultStorage')

        # File storage can either be a Storage instance (currently deprecated),
        # or a class which we should instantiate ourselves
        file_storage = import_class(file_storage_class)
        if isinstance(file_storage, type):
            # The class case
            file_storage = file_storage()
        self.file_storage = file_storage

    def get_file(self):
        """
        Return file object
        """
        return self.upload_file

    def get_full_path(self):
        """
        Return full path for file:
        /REDACTOR_UPLOAD/filename.etc
        """
        return os.path.join(self.get_upload_path(), self.get_filename())

    def save_file(self):
        """
        Save file and return real path
        """
        if not hasattr(self, 'real_path'):
            self.real_path = self.file_storage.save(self.get_full_path(),
                                                    self.get_file())
        return self.real_path

    def get_url(self):
        """
        Return url for file if he saved else None
        """
        if getattr(settings, 'MEDIA_URL') is None:
            raise ValueError('MEDIA_URL should be set')

        base_url = os.path.join(
            settings.MEDIA_URL,
            getattr(settings, 'REDACTOR_UPLOAD', 'redactor/')
        )

        return urljoin(
            base_url,
            self.get_filename()
        )

    def get_filename(self):
        """
        Should return the file name
        """
        raise NotImplementedError

    def get_upload_path(self):
        """
        Should return the directory for file storage
        """
        raise NotImplementedError

    @staticmethod
    def get_default_upload_path():
        if getattr(settings, 'MEDIA_ROOT') is None:
            raise ValueError('MEDIA_ROOT should be set')
        return os.path.join(settings.MEDIA_ROOT, getattr(settings, 'REDACTOR_UPLOAD', 'redactor'))


class SimpleUploader(BaseUploaderRedactor):
    """
    Standard uploader: default directory, default name
    """
    def get_filename(self):
        return self.upload_file.name

    def get_upload_path(self):
        return self.upload_to or self.get_default_upload_path()


class UUIDUploader(SimpleUploader):
    """
    Handler that renames files based on UUID

    /REDACTOR_UPLOAD/546de5b5-cf05-4b47-9379-3f964732b802.etc
    """
    def get_filename(self):
        if not hasattr(self, 'filename'):
            # save filename prevents the generation of a new
            extension = self.upload_file.name.split('.')[-1]
            self.filename = '{0}.{1}'.format(uuid.uuid4(), extension)
        return self.filename


class DateDirectoryUploader(SimpleUploader):
    """
    Handler  that saves files in a directory based on the current date

    <MEDIA_ROOT>/<REDACTOR_UPLOAD>/2014/3/28/filename.etc
    """
    def get_upload_path(self):
        path = super().get_default_upload_path()
        today = datetime.date.today()
        path = os.path.join(path, str(today.year), str(today.month), str(today.day))
        return path
