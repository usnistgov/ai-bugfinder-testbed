""" Abstract classes for creating processing steps.
"""

from abc import abstractmethod
from random import randint
from time import sleep

from bugfinder.base.processing import AbstractProcessing
from bugfinder.settings import LOGGER
from bugfinder.utils.containers import start_container, stop_container_by_name
from bugfinder.utils.rand import get_rand_string


class AbstractContainerProcessing(AbstractProcessing):
    """Abstract class for processing data using a Docker container."""

    start_retries = 3
    image_name = ""
    container_name = ""
    container_ports = None
    machine_ports = None
    volumes = None
    environment = None
    command = None
    detach = True

    container = None

    def execute(self, command_args=None, container_config=None):
        """Execute the processing using the processing container.

        Args:
            command_args:
            container_config:
        """
        try:
            # Handle container configuration depending on wether a manual configuration
            # has been provided or not
            if container_config is None:
                self.configure_container()
            else:
                self.configure_container_with_dict(container_config)
            started = False

            self.container_name = "%s-%s" % (
                self.container_name,
                get_rand_string(6, special=False, upper=False),
            )

            if command_args is not None:
                self.configure_command(command_args)

            while not started:
                try:
                    self.container = start_container(
                        self.image_name,
                        self.container_name,
                        self.assign_ports(),
                        self.volumes,
                        self.environment,
                        self.command,
                        self.detach,
                    )

                    started = True
                except Exception as exc:  # Restart the container if an error occured
                    LOGGER.error(
                        "An exception has occured while starting the container: %s.",
                        str(exc),
                    )
                    sleep(5)
                    self.start_retries -= 1

                    if self.start_retries == 0:
                        raise exc

            self.send_commands()
        except Exception as exc:
            LOGGER.error("Error while running commands: %s.", str(exc))
            raise exc
        finally:
            if self.container is not None and self.detach:
                stop_container_by_name(self.container_name)

    def assign_ports(self):
        """Randomly assign ports on the machine."""
        assigned_ports = None
        if self.container_ports is not None:
            self.machine_ports = [
                "%d" % randint(49152, 65535) for _ in self.container_ports
            ]
            assigned_ports = dict(zip(self.container_ports, self.machine_ports))

        return assigned_ports

    @abstractmethod
    def configure_container(self):  # pragma: no cover
        """Configure the given container automatically. Needs to be implemented by the
        subclass.
        """
        raise NotImplementedError("Method 'configure_container' not implemented.")

    def configure_container_with_dict(self, container_config):
        """Configure the given container manually. Needs to be implemented by the
        subclass.

        Args:
            container_config:
        """
        LOGGER.warning(
            "Manual configuration is not handled by the container. The class should "
            "implement 'configure_container_with_dict(self, container_config)' to handle"
            "manual configuration"
        )
        return self.configure_container()

    def configure_command(self, command):
        """Configure the command to be sent to the container. Needs to be implemented
        by the subclass.

        Args:
            command:
        """
        raise Exception("Command %s not handled by container")

    @abstractmethod
    def send_commands(self):  # pragma: no cover
        """Send the commands to container. Needs to be implemented by the subclass."""
        raise NotImplementedError("Method 'send_commands' not implemented.")
