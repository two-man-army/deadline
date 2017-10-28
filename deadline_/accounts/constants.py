NOTIFICATION_TOKEN_EXPIRY_MINUTES = 1440
NOTIFICATION_SECRET_KEY = 't0ps3cr3t123'  # TODO: Load from env
FACEBOOK_PROFILE_REGEX = r'^(?:http(s)?:\/\/)?(?:www\.)?facebook\.com\/(?:(?:\w)*#!\/)?(?P<page_name>[\w\-]{1,50})(((?=\/).+\/(?!\/))|(?!\/)|(\/?\?.+))$'
TWITTER_PROFILE_REGEX = r'^(?:http(s)?:\/\/)?(?:www\.)?twitter\.com\/(?:(?:\w)*#!\/)?(?P<profile_name>[\w\-]{1,50})(\?[^\/]+)?$'
GITHUB_PROFILE_REGEX = r'^(?:http(s)?:\/\/)?(?:www\.)?github\.com\/(?:(?:\w)*#!\/)?(?P<profile_name>[\w\-]{1,50})(\?[^\/]+)?$'
LINKEDIN_PROFILE_REGEX = r'^(?:http(s)?:\/\/)?(?:www\.)?linkedin\.com\/in/(?P<profile_name>[\w\-]{1,50})(\?[^\/]+)?/?$'
