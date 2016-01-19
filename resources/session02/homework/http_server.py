import socket
import sys
import mimetypes
from pathlib import Path


def response_ok(body=b"this is a pretty minimal response", mimetype=b"text/plain"):
    """returns a basic HTTP response"""

    body, mimetype = resolve_uri(body)
    resp = []
    resp.append(b"HTTP/1.1 200 OK")
    resp.append(b"Content-Type: " + mimetype)
    resp.append(b"")
    resp.append(body)
    return b"\r\n".join(resp)


def response_method_not_allowed():
    """returns a 405 Method Not Allowed response"""
    resp = []
    resp.append("HTTP/1.1 405 Method Not Allowed")
    resp.append("")
    return "\r\n".join(resp).encode('utf8')


def response_not_found():
    """returns a 404 Not Found response"""
    resp = []
    resp.append("HTTP/1.1 404 Not Found")
    resp.append("")
    return "\r\n".join(resp).encode('utf8')


def parse_request(request):
    first_line = request.split("\r\n", 1)[0]
    method, uri, protocol = first_line.split()
    if method != "GET":
        raise NotImplementedError("We only accept GET")
    return uri


def resolve_uri(uri):
    """This method should return appropriate content and a mime type"""
    contents = b''
    mimetype = b''
    directory = './webroot'

    if isinstance(uri, bytes):
        directory += str(uri.decode('utf8'))
    else:
        directory += str(uri)

    try:
        pathreq = Path(directory).resolve()  # Attempt to resolve the requested directory

        if pathreq.exists():
            if pathreq.is_dir():
                # The requested path maps to a directory. The content should be a
                # plain-text listing of the directory contents with a mimetype of text/plain.
                filelist = [str(files) for files in pathreq.iterdir() if files.is_file()]
                contents = '\n'.join(filelist).encode('utf8')
                mimetype = b'text/plain'
            else:
                # The requested path maps to a file
                contents = pathreq.read_bytes()
                mimetype = mimetypes.guess_type(str(pathreq))[0].encode('utf8')
        else:
            raise NameError("{} does not exist\n".format(pathreq))
    except FileNotFoundError:
        raise NameError("{} could not be resolved\n".format(directory))
    except:
        print("Unexpected error:{}\n".format(sys.exc_info()[0]))

    return contents, mimetype


def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)
                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')
                    if len(data) < 1024:
                        break

                try:
                    uri = parse_request(request)
                except NotImplementedError:
                    response = response_method_not_allowed()
                else:
                    try:
                        content, mime_type = resolve_uri(uri)
                    except NameError:
                        response = response_not_found()
                    else:
                        response = response_ok(content, mime_type)

                print('sending response', file=log_buffer)
                conn.sendall(response)
            finally:
                conn.close()

    except KeyboardInterrupt:
        sock.close()
        return


if __name__ == '__main__':
    server()
    sys.exit(0)
