#!/usr/bin/env python
""" md5s3stash
    content addressable storage in AWS S3
"""
import urllib.parse
import logging
import hashlib
import boto3
from botocore.errorfactory import ClientError
import magic
from PIL import Image
from collections import namedtuple


def md5s3stash(file_path, bucket_base):
    """ stash a file at `file_path` in the named `bucket_base` """
    StashReport = namedtuple(
        'StashReport', 'url, md5, s3_url, mime_type, dimensions')
    md5 = hashChunks(file_path)
    s3_url = "s3://{0}/{1}".format(bucket_base,md5)
    (mime, dimensions) = image_info(file_path)
    s3move(file_path, s3_url, mime)
    report = StashReport(file_path, md5, s3_url, mime, dimensions)
    logging.getLogger('MD5S3:stash').info(report)
    return report


def hashChunks(file_path):
    """
       Helper to return an md5 checksum

       based on downloadChunks@https://gist.github.com/gourneau/1430932
       and http://www.pythoncentral.io/hashing-files-with-python/
    """
    hasher = hashlib.new('md5')
    BLOCKSIZE = 1024 * hasher.block_size
    try:
        with open(file_path, 'r') as file:
            while True:
                chunk = file.read(BLOCKSIZE)
                hasher.update(chunk)
                if not chunk:
                    break
    except IOError as e:
        print("Could not open file", e, file_path)
        return False

    md5 = hasher.hexdigest()
    return md5


def s3move(file_path, s3_url, mime):
    s3 = boto3.client('s3')
    l = logging.getLogger('MD5S3:s3move')
    l.debug({
        'file_path': file_path,
        's3_url': s3_url,
        'mime': mime,
        's3': s3
    })
    parts = urllib.parse.urlsplit(s3_url)
    try:
        s3.head_object(Bucket=parts.netloc, Key=parts.path[1:])
        l.info('key existed already')
    except ClientError:
        public_read = 'uri="http://acs.amazonaws.com/groups/global/AllUsers"'
        s3.upload_file(file_path, parts.netloc, parts.path[1:], 
            ExtraArgs={
                'GrantRead': public_read, 
                'GrantFullControl': settings.S3_ID, 
                'ContentType': mime
            })
        l.debug('file sent to s3')

def image_info(filepath):
    ''' get image info
        `filepath` path to a file
        returns
          a tuple of two values
            1. mime/type if an image; otherwise None
            2. a tuple of (height, width) if an image; otherwise (0,0)
    '''
    try:
        return (
            magic.Magic(mime=True).from_file(filepath),
            Image.open(filepath).size
        )
    except IOError as e:
        if not e.message.startswith('cannot identify image file'):
            raise e
        else:
            return (None, (0,0))


