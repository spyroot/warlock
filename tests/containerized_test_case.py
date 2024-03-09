"""
Adds addition method to unittest for IO checks,
setup docker container.

Note unit test depends on docker container that we use to test ssh etc.
hence make sure it installed.

to access docker container use self.container_id
to access ssh port exposed use self.ssh_port

Author: Mustafa Bayramov
spyroot@gmail.com
mbayramo@stanford.edu
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List

from tests.extended_test_case import ExtendedTestCase


def generate_docker_file():
    """By default it just ubuntu latest docker image"""
    return """
FROM ubuntu:latest
RUN apt-get update && apt-get install -y openssh-server
RUN mkdir /var/run/sshd

RUN useradd -ms /bin/bash sshuser && \
    echo 'sshuser:sshpass' | chpasswd

RUN mkdir -p /home/sshuser/.ssh && \
    ssh-keygen -t rsa -f /home/sshuser/.ssh/id_rsa -q -N ""

RUN chown -R sshuser:sshuser /home/sshuser/.ssh && \
    chmod 700 /home/sshuser/.ssh && \
    chmod 600 /home/sshuser/.ssh/*

RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
"""


def get_container_id_by_image_tag(
        image_tag: str
) -> List[str]:
    """Return the container ID of the container with the specified image tag."""
    try:
        cmd = f"docker ps --filter ancestor={image_tag}" + " --format {{.ID}}"
        output = subprocess.check_output(
            cmd,
            shell=True
        )
        if output is not None:
            output = output.decode('utf-8').strip()
            container_ids = output.split()
            if len(container_ids) == 0:
                return []
            else:
                return container_ids
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while getting the container ID: {e}")
        return []

    return []


class ContainerizedTestCase(ExtendedTestCase):
    """
    ContainerizedTestCase represent a test case that relay on some container
    that test case require.
    """
    image_tag = 'test_ssh_server:latest'
    _container_id = None
    _ssh_port = None
    _ssh_pass = 'sshpass'
    _ssh_user = 'sshuser'

    @classmethod
    def _build_container(cls):
        """Build the Docker container."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(generate_docker_file().encode('utf-8'))
            dockerfile_path = tmp_file.name

        dockerfile_path = Path(dockerfile_path).resolve().absolute()
        build_command = f'docker build -t {cls.image_tag} -f {dockerfile_path} .'
        try:
            _ = subprocess.run(
                build_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )

        except subprocess.CalledProcessError as e:
            if "Cannot connect to the Docker daemon" in str(e) or "error" in str(e):
                raise Exception("Cannot connect to the Docker daemon. Is the Docker daemon running?")
            else:
                raise

        os.remove(dockerfile_path)

    @classmethod
    def _stop_and_remove_container(cls):
        """Stop and remove the Docker container."""
        try:
            running_containers = subprocess.check_output(
                'docker ps -q --filter "id=' + cls._container_id + '"',
                shell=True
            ).decode('utf-8').strip().split()

            for container_id in running_containers:
                subprocess.run(f'docker stop {container_id}', shell=True, check=True)

            subprocess.run(f'docker rm {cls._container_id}', shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while stopping and removing the container: {e}")

    @classmethod
    def _stop_and_remove_containers(cls):
        """Stop and remove all Docker containers with the ancestor test_ssh_server:latest."""
        try:
            containers = get_container_id_by_image_tag(cls.image_tag)
            for container_id in containers:
                container_id = container_id.strip()
                subprocess.run(f'docker stop {container_id}', shell=True, check=True)
                subprocess.run(f'docker rm {container_id}', shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while stopping and removing the containers: {e}")

    @classmethod
    def setUpClass(cls):
        """During setup procedure we build container that later used by classes that extends
        ContainerizedTestCase as part of unit tests.
        :return:
        """
        if os.environ.get('REBUILD_CONTAINER') == 'true':
            cls.rebuild_container()
        else:
            cls._build_container()

        cls._container_id = subprocess.check_output(
            f'docker run -d -P {cls.image_tag}', shell=True
        ).decode('utf-8').strip()

        if cls._container_id is None:
            raise ValueError(f"Invalid Docker container ID it unexpected")

        if len(cls._container_id) != 64:
            raise ValueError(f"Invalid Docker container ID length: {cls._container_id}")

        cls._ssh_port = subprocess.check_output(
            f"docker port {cls._container_id} 22",
            shell=True
        ).decode('utf-8').split(':')[1].strip()

    @classmethod
    def rebuild_container(cls):
        """Rebuild the Docker container."""
        # Stop and remove the existing container
        cls._stop_and_remove_container()

        # Build a new container
        cls._build_container()

        # Start the new container
        cls._container_id = subprocess.check_output(
            f'docker run -d -P {cls.image_tag}', shell=True
        ).decode('utf-8').strip()

        if cls._container_id is None:
            raise ValueError(f"Invalid Docker container ID, it is unexpected.")

        if len(cls._container_id) != 64:
            raise ValueError(f"Invalid Docker container ID length: {cls._container_id}")

        cls._ssh_port = subprocess.check_output(
            f"docker port {cls._container_id} 22",
            shell=True
        ).decode('utf-8').split(':')[1].strip()

    @classmethod
    def tearDownClass(cls):
        """
        :return:
        """
        cls._stop_and_remove_containers()

    @property
    def container_id(self):
        """Publicly accessible container_id property."""
        if self._container_id is None:
            raise ValueError("Container ID has not been set.")
        return self._container_id

    @property
    def ssh_port(self):
        """Publicly accessible ssh_port property."""
        if self._ssh_port is None:
            raise ValueError("SSH port has not been determined.")
        return self._ssh_port

    @property
    def ssh_pass(self):
        """Publicly accessible ssh_pass property."""
        return self._ssh_pass

    @property
    def ssh_user(self):
        """Publicly accessible ssh_user property."""
        return self._ssh_user
