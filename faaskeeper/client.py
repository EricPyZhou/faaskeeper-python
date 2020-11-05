
import uuid

from faaskeeper.response import ResponseHandler
from faaskeeper.providers.aws import AWSClient

class FaaSKeeperClient:

    _providers = {
        "aws": AWSClient
    }

    def __init__(self, provider: str, service_name: str, port: int = -1, verbose: bool = False):
        self._client_id = str(uuid.uuid4())[0:8]
        self._service_name = service_name
        self._session_id = None
        #self._writer_queue = []
        self._write_requests_count = 0
        self._provider_client = FaaSKeeperClient._providers[provider](verbose)
        self._port = port

    def start(self):
        """
            1) Start thread handling replies from FK.
            2) Start heartbeat thread
            3) Add yourself to the FK service.
        """
        self._session_id = str(uuid.uuid4())[0:8]
        self._response_handler = ResponseHandler(self._port)
        self._response_handler.start()

    def stop(self):
        """
            Before shutdown:
            1) Wait for pending requests.
            2) Notify system about closure.
            3) Stop heartbeat thread
        """
        # notify service about closure
        self._session_id = None
        self._write_requests_count = 0

    # TODO: sequence nodes
    # TODO: ephemeral nodes
    # TODO: ACL
    # TODO: makepath
    # TODO: async call with callback + ctx
    def create(self, path: str, value: str = b"", acl: str = None,
            ephemeral: bool = False, sequence: bool = False,
            makepath: bool = False) -> str:
        self._provider_client.send_request(
            table=f"{self._service_name}-write-queue",
            service_name=self._service_name,
            request_id=f"{self._session_id}-{self._write_requests_count}",
            data={
                "op": "create_node",
                "path": path,
                "user": self._session_id,
                "version": -1,
                "flags": 0,
                "data": value,
                "sourceIP": self._response_handler.address,
                "sourcePort": self._response_handler.port
            }
        )
        #self._writer_queue.append(f"{self._session_id}-{self._write_requests_count}")
        self._write_requests_count += 1

        self._response_handler.stop()

