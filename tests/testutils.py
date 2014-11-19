import urlparse
import requests
import json


FAKE_FS = {
        'a/b/c.txt': 'This is a/b/c.txt',
        'b.txt': 'This is b.txt'
}

def fake_response(status_code, content):
    '''Returns a fake requests.Response object'''
    r = requests.Response()
    r.status_code = status_code
    r._content = content
    return r


def stubbed_get(url):
    '''Stub for requests.get which imitates HTTPFS.'''
    prefix = 'http://localhost:14000/webhdfs/v1/'
    if not url.startswith(prefix):
        raise requests.ConnectionError()

    parsed_url = urlparse.urlparse(url)
    assert parsed_url.path.startswith('/webhdfs/v1/')
    path = parsed_url.path[len('/webhdfs/v1/'):]

    q = dict(urlparse.parse_qsl(parsed_url.query))
    assert 'op' in q
    assert 'user.name' in q

    if path in FAKE_FS:
        r = fake_response(200, FAKE_FS[path])
    else:
        return fake_response(404, json.dumps({
            'RemoteException': {
                'message': 'File /%s does not exist.' % path,
                'exception': 'FileNotFoundException'
            }
        }))

    if q['op'].lower() == 'open':
        if q.get('offset'):
            r._content = r._content[int(q.get('offset')):]
        if q.get('length'):
            r._content = r._content[:int(q.get('length'))]
    elif q['op'].lower() == 'getcontentsummary':
        if r.status_code == 200:
            r._content = json.dumps({'ContentSummary':{'length':len(r._content)}})
    else:
        raise ValueError('Invalid op %s' % q['op'])
    return r
