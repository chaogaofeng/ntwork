def upload_file(file_path, file_name):
    import oss2

    # 阿里云OSS配置
    access_key_id = ''
    access_key_secret = ''
    endpoint = 'https://oss-cn-hangzhou.aliyuncs.com'  # 比如oss-cn-shanghai.aliyuncs.com
    bucket_name = 'ntwork'

    # 初始化OSS
    auth = oss2.Auth(access_key_id, access_key_secret)
    # 初始化bucket
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    try:
        bucket.get_bucket_info()
    except:
        # 创建 bucket
        bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ)

    bucket.put_object_from_file(file_name, file_path)

    print(f'upload completed. https://{bucket_name}.oss-cn-hangzhou.aliyuncs.com/{file_name}')


if __name__ == '__main__':
    upload_file('README.md', 'README.md')
