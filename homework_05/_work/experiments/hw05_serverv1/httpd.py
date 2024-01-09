import argparse
import logging
import mimetypes
import os
import posixpath
import socket
import sys
import time

from queue import Queue
from threading import Thread


logging.basicConfig(format='[%(asctime)s] %(levelname)s %(message)s', level=logging.INFO,

                    datefmt='%a %b %d %H:%M:%S %Y')


class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                logging.error(e)
            self.tasks.task_done()


class ThreadPool:
    """Pool of threads consuming tasks from a queue"""

    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()


class WebServer(ThreadPool):

    def __init__(self, port=8080, doc_root="DOCUMENT_ROOT", workers=1):
        super().__init__(workers)
        self.host = socket.gethostname().split('.')[0]
        self.port = port
        self.doc_root = doc_root
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.workers = workers

    def start(self):
        """
        Attempts to create and bind a socket to launch the server
        """
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            logging.info("Starting server on {host}:{port}".format(host=self.host, port=self.port))
            self.socket.bind((self.host, int(self.port)))
            logging.info("Server started on port {port}.".format(port=self.port))
        except Exception as e:
            logging.info("Error: Could not bind to port {port}".format(port=self.port))
            logging.info(e)
            self.shutdown()
            sys.exit(1)
        else:
            self._listen()  # Start listening for connections

    def shutdown(self):
        """
        Shutdown server
        """
        try:
            logging.info("Shutting down server")
            self.socket.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            pass  # Pass if socket is already closed

    def _generate_headers(self, response_code, request_file=""):
        """
        Generate HTTP response headers.
        Parameters:
            - response_code: HTTP response code to add to the header. 200 and 404 supported
            - request_file: Path to requested file
        Returns:
            A formatted HTTP header for the given response_code
        """
        header = ''
        if response_code == 200:
            header += 'HTTP/1.1 200 OK\n'
            mimetype = mimetypes.types_map[os.path.splitext(request_file)[1]]
            header += 'Content-length: {}\n'.format(str(os.path.getsize(request_file)))
            header += 'Content-type: {}\n'.format(mimetype)

        elif response_code == 404:
            header += 'HTTP/1.1 404 Not Found\n'
        elif response_code == 400:
            header += 'HTTP/1.1 400 Bad request\n'
        # How to count content length
        time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        header += 'Date: {now}\n'.format(now=time_now)
        header += 'Server: Mikhail Samoylov for Otus Python Server\n'
        header += 'Connection: close\n\n'  # Signal that connection will be closed after completing the request
        return header

    def _listen(self):
        """
        Listens on self.port for any incoming connections
        """
        self.socket.listen(5)
        while True:
            (client, address) = self.socket.accept()
            client.settimeout(60)
            logging.info("Recieved connection from {addr}".format(addr=address))
            self.add_task(self._handle_client, client, address)
            self.wait_completion()

    def _handle_client(self, client, address):
        """
        Main loop for handling connecting clients and serving files from DOCUMENT_ROOT
        Parameters:
            - client: socket client from accept()
            - address: socket address from accept()
        """
        PACKET_SIZE = 1024
        while True:
            logging.info("CLIENT: {c}".format(c=client))
            data = client.recv(PACKET_SIZE).decode()  # Recieve data packet from client and decode

            if not data:
                break

            request_method = data.split(' ')[0]
            logging.info("Method: {m}".format(m=request_method))
            logging.info("Request Body: {b}".format(b=data))

            if request_method == "GET" or request_method == "HEAD":
                # Ex) "GET /index.html" split on space
                file_requested = data.split(' ')[1]

                # If get has parameters ('?'), ignore them
                file_requested = file_requested.split('?')[0]
                file_requested = posixpath.normpath(file_requested)
                if file_requested == "/":
                    file_requested = "/index.html"
                elif file_requested == "/directory/":
                    file_requested = "/directory/index.html"

                filepath_to_serve = self.doc_root + file_requested
                logging.info("Serving web page [{fp}]".format(fp=filepath_to_serve))

            # Load and Serve files content
                try:
                    with open(filepath_to_serve, 'rb') as f:
                        if request_method == "GET":  # Read only for GET
                            response_data = f.read()
                    response_header = self._generate_headers(200, filepath_to_serve)

                except Exception as e:
                    logging.info("File not found. Serving 404 page.")
                    response_header = self._generate_headers(404)

                    if request_method == "GET":  # Temporary 404 Response Page
                        response_data = '<html><body><center><h3>Error 404: File not found</h3><p>' \
                                        'Python HTTP Server</p></center></body></html>'.encode()
                response = response_header.encode()
                if request_method == "GET":
                    response += response_data

                client.send(response)
                client.close()
                break
            else:
                response_header = self._generate_headers(405)
                response_data = '<html><body><center><h3>Error 405: Method not allowed</h3><p>' \
                                    'Python HTTP Server</p></center></body></html>'.encode()
                response = response_header.encode()
                response += response_data
                client.send(response)
                client.close()
                logging.error("Unknown HTTP request method: {method}".format(method=request_method))
                break


def parse_args():
    parser = argparse.ArgumentParser(
        description='Web Server For Education.')
    parser.add_argument("--p", dest="port", help="Server port.",
                        default=8080)
    parser.add_argument("--w", dest="workers", help="Workers count",
                        default=1)
    parser.add_argument("--r", dest="doc_root", help="Document Root directory.",
                        default="DOCUMENT_ROOT")
    return parser.parse_args()


def main():
    options = parse_args()
    server = WebServer(options.port, options.doc_root, int(options.workers))
    try:
        server.start()
        logging.info("Press Ctrl+C to shut down server.")
    except KeyboardInterrupt:
        server.shutdown()
        logging.info("User stopped server process.")


if __name__ == "__main__":
    main()