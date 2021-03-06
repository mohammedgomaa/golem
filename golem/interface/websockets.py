import sys

from twisted.internet.defer import Deferred

from golem.rpc.cert import CertificateManager
from golem.rpc.common import CROSSBAR_REALM, CROSSBAR_PORT, CROSSBAR_HOST
from golem.rpc.session import Session, ClientProxy, WebSocketAddress


class WebSocketCLI(object):
    class NoConnection(object):

        def __getattribute__(self, item):
            raise Exception("Cannot connect to Golem instance")

    class CLIClient(ClientProxy):

        def _call(self, method_alias, *args, **kwargs):
            from twisted.internet import reactor
            deferred = Deferred()

            super_call = super()._call

            def in_reactor():
                try:
                    parent_deferred = super_call(
                        method_alias,
                        *args,
                        **kwargs,
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    deferred.errback(exc)
                else:
                    parent_deferred.chainDeferred(deferred)

            reactor.callFromThread(in_reactor)
            return deferred

    def __init__(self, cli,  # pylint: disable=too-many-arguments
                 cert_manager: CertificateManager,
                 host: str = CROSSBAR_HOST,
                 port: int = CROSSBAR_PORT,
                 realm: str = CROSSBAR_REALM,
                 ssl: bool = True) -> None:

        address = WebSocketAddress(host, port, realm, ssl)

        self.cli = cli

        crsb_user = cert_manager.CrossbarUsers.golemcli
        self.session = Session(
            address,
            crsb_user=crsb_user,
            crsb_user_secret=cert_manager.get_secret(crsb_user)
        )

    def execute(self, *args, **kwargs):
        from twisted.internet import reactor, threads

        def on_ready(_):
            threads.deferToThread(self.cli.execute, *args, **kwargs) \
                .addBoth(self.shutdown)

        def on_connected(_):
            core_client = WebSocketCLI.CLIClient(self.session)
            self.cli.register_client(core_client)
            core_client._ready.addCallback(on_ready)  # noqa pylint: disable=protected-access

        def on_error(error):
            sys.stderr.write("Error connecting to Golem instance ({}): {}\n"
                             .format(self.session.address, error))

            self.cli.register_client(WebSocketCLI.NoConnection())
            self.cli.execute(*args, **kwargs)
            self.shutdown()

        def connect():
            self.session.connect(
                auto_reconnect=False
            ).addCallbacks(on_connected, on_error)

        reactor.callWhenRunning(connect)
        reactor.run()

    def shutdown(self, *_):
        from twisted.internet import reactor
        from twisted.internet.error import ReactorNotRunning

        if self.cli:
            self.cli.shutdown()
        if self.session:
            self.session.disconnect()

        try:
            reactor.stop()
        except ReactorNotRunning:
            pass
