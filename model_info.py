
class ModelInfo(object):
    def __init__(
            self,
            model_id,
            title,
            attribution_url,
            owner_username,
            license_url,
            domain,
            scope,
            file_type,
            download_path,
            search_index,
    ):
        self.model_id = model_id
        self.title = title
        self.attribution_url = attribution_url
        self.owner_username = owner_username
        self.license_url = license_url
        self.domain = domain
        self.scope = scope
        self.file_type = file_type
        self.download_path = download_path
        self.search_index = search_index