import re
import socket
import http.client as httplib
import unittest

from src.config import config


class HttpServer(unittest.TestCase):
    host = "localhost"
    port = config.PORT

    def setUp(self):
        self.conn = httplib.HTTPConnection(self.host, self.port, timeout=10)

    def tearDown(self):
        self.conn.close()

    def test_empty_request(self):
        """ Send bad http headers """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(b"\n")
        s.close()

    def test_server_header(self):
        """Server header exists"""
        self.conn.request("GET", "/httptest/")
        resp = self.conn.getresponse()
        resp.read()
        server = resp.getheader("Server")
        self.assertIsNotNone(server)

    def test_directory_index(self):
        """directory index file exists"""
        self.conn.request("GET", "/httptest/dir2/")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 34)
        self.assertEqual(len(data), 34)
        self.assertEqual(data, b"<html>Directory index file</html>\n")

    def test_index_not_found(self):
        """directory index file absent"""
        self.conn.request("GET", "/httptest/dir1/")
        resp = self.conn.getresponse()
        resp.read()
        self.assertEqual(int(resp.status), 404)

    def test_file_not_found(self):
        """absent file returns 404"""
        self.conn.request(
          "GET", "/httptest/smdklcdsmvdfjnvdfjvdfvdfvdsfssdmfdsdfsd.html")
        resp = self.conn.getresponse()
        resp.read()
        self.assertEqual(int(resp.status), 404)

    def test_file_in_nested_folders(self):
        """file located in nested folders"""
        self.conn.request("GET", "/httptest/dir1/dir12/dir123/deep.txt")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 20)
        self.assertEqual(len(data), 20)
        self.assertEqual(data, b"bingo, you found it\n")

    def test_file_with_slash(self):
        """slash after filename"""
        self.conn.request("GET", "/httptest/dir2/page.html/")
        resp = self.conn.getresponse()
        resp.read()
        self.assertEqual(int(resp.status), 404)

    def test_file_with_query_string(self):
        """query string after filename"""
        self.conn.request("GET",
                          "/httptest/dir2/page.html?arg1=value&arg2=value")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 38)
        self.assertEqual(len(data), 38)
        self.assertEqual(data, b"<html><body>Page Sample</body></html>\n")

    def test_file_with_spaces(self):
        """filename with spaces"""
        self.conn.request("GET", "/httptest/space%20in%20name.txt")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 19)
        self.assertEqual(len(data), 19)
        self.assertEqual(data, b"letters and spaces\n")

    def test_file_urlencoded(self):
        """urlencoded filename"""
        self.conn.request("GET", "/httptest/dir2/%70%61%67%65%2e%68%74%6d%6c")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 38)
        self.assertEqual(len(data), 38)
        self.assertEqual(data, b"<html><body>Page Sample</body></html>\n")

    def test_large_file(self):
        """large file downloaded correctly"""
        self.conn.request("GET", "/httptest/wikipedia_russia.html")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 954824)
        self.assertEqual(len(data), 954824)
        self.assertIn(b"Wikimedia Foundation, Inc.", data)

    def test_document_root_escaping(self):
        """document root escaping forbidden"""
        self.conn.request(
          "GET", "/httptest/../../../../../../../../../../../../../etc/passwd")
        resp = self.conn.getresponse()
        resp.read()
        self.assertIn(int(resp.status), (400, 403, 404))

    def test_file_with_dot_in_name(self):
        """file with two dots in name"""
        self.conn.request("GET", "/httptest/text..txt")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        self.assertEqual(int(resp.status), 200)
        self.assertIn(b"hello", data)
        self.assertEqual(int(length), 5)

    def test_post_method(self):
        """post method forbidden"""
        self.conn.request("POST", "/httptest/dir2/page.html")
        r = self.conn.getresponse()
        r.read()
        self.assertIn(int(r.status), (400, 405))

    def test_head_method(self):
        """head method support"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send(b"HEAD /httptest/dir2/page.html HTTP/1.0\r\n\r\n")
        data = b""
        while 1:
            buf = s.recv(1024)
            if not buf:
              break
            data += buf
        s.close()

        self.assertTrue(data.find(b"\r\n\r\n") > 0,
                        "no empty line with CRLF found")
        (head, body) = re.split(b"\r\n\r\n", data, 1)
        headers = head.split(b"\r\n")
        self.assertTrue(len(headers) > 0, "no headers found")

        status_line = headers.pop(0)
        (proto, code, status) = status_line.split(b" ")
        h = {}
        for k, v in enumerate(headers):
            (name, value) = re.split(b'\s*:\s*', v, 1)
            h[name] = value
        if int(code) == 200:
            self.assertEqual(int(h[b'Content-Length']), 38)
            self.assertEqual(len(body), 0)
        else:
            self.assertIn(int(code), (400, 405))

    def test_filetype_html(self):
        """Content-Type for .html"""
        self.conn.request("GET", "/httptest/dir2/page.html")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        ctype = resp.getheader("Content-Type")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 38)
        self.assertEqual(len(data), 38)
        self.assertEqual(ctype, "text/html")

    def test_filetype_css(self):
        """Content-Type for .css"""
        self.conn.request("GET", "/httptest/splash.css")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        ctype = resp.getheader("Content-Type")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 98620)
        self.assertEqual(len(data), 98620)
        self.assertEqual(ctype, "text/css")

    def test_filetype_js(self):
        """Content-Type for .js"""
        self.conn.request("GET", "/httptest/jquery-1.9.1.js")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        ctype = resp.getheader("Content-Type")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 268381)
        self.assertEqual(len(data), 268381)
        self.assertIn(ctype, (
          "application/x-javascript",
          "application/javascript",
          "text/javascript"))

    def test_filetype_jpg(self):
        """Content-Type for .jpg"""
        self.conn.request("GET", "/httptest/160313.jpg")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        ctype = resp.getheader("Content-Type")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 267037)
        self.assertEqual(len(data), 267037)
        self.assertEqual(ctype, "image/jpeg")

    def test_filetype_jpeg(self):
        """Content-Type for .jpeg"""
        self.conn.request("GET", "/httptest/ef35c.jpeg")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        ctype = resp.getheader("Content-Type")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 160462)
        self.assertEqual(len(data), 160462)
        self.assertEqual(ctype, "image/jpeg")

    def test_filetype_png(self):
        """Content-Type for .png"""
        self.conn.request("GET", "/httptest/logo.v2.png")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        ctype = resp.getheader("Content-Type")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 1754)
        self.assertEqual(len(data), 1754)
        self.assertEqual(ctype, "image/png")

    def test_filetype_gif(self):
        """Content-Type for .gif"""
        self.conn.request("GET", "/httptest/pic_ask.gif")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        ctype = resp.getheader("Content-Type")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 1747)
        self.assertEqual(len(data), 1747)
        self.assertEqual(ctype, "image/gif")

    def test_filetype_swf(self):
        """Content-Type for .swf"""
        self.conn.request("GET", "/httptest/b16261023.swf")
        resp = self.conn.getresponse()
        data = resp.read()
        length = resp.getheader("Content-Length")
        ctype = resp.getheader("Content-Type")
        self.assertEqual(int(resp.status), 200)
        self.assertEqual(int(length), 35344)
        self.assertEqual(len(data), 35344)
        self.assertEqual(ctype, "application/x-shockwave-flash")


loader = unittest.TestLoader()
suite = unittest.TestSuite()
a = loader.loadTestsFromTestCase(HttpServer)
suite.addTest(a)


class NewResult(unittest.TextTestResult):
    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        return doc_first_line or ""


class NewRunner(unittest.TextTestRunner):
    resultclass = NewResult


runner = NewRunner(verbosity=2)
runner.run(suite)
