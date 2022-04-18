import epo_ops


def _make_request(self, url, data, extra_headers=None, params=None, use_get=False):

    token = "Bearer {0}".format(self.access_token.token)
    headers = {
        "Accept": self.accept_type,
        "Content-Type": "text/plain",
        "Authorization": token,
    }
    headers.update(extra_headers or {})
    request_method = self.request.post
    if use_get:
        request_method = self.request.get

    response = request_method(url, data=data, headers=headers, params=params)
    response = self._check_for_expired_token(response)
    response = self._check_for_exceeded_quota(response)

    # !!! PATCH !!!
    # Let errors propagate. Don't croak on anything status >= 400.
    # response.raise_for_status()

    return response


# Monkeypatch original `epo_ops_client` not to use `response.raise_for_status()`
# by default. This enables downstream error handling.
epo_ops.Client._make_request = _make_request
