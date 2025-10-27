# Containerization

## Docker on Linux

The text below shows how you can use (code of) the ICOtronic package in a Docker container on a **Linux host**. The description on how to move the interface of the Docker container is an adaption of an [article/video from the “Chemnitzer Linux-Tage”](https://chemnitzer.linux-tage.de/2021/de/programm/beitrag/210).

### Creating a Docker Image

To create a Docker image that contains ICOtronic just install the package with `pip` inside your `Dockerfile`. We recommend that you use a virtual environment to install the package. For an example, please take a look at our [`Dockerfile`](https://github.com/MyTooliT/ICOtronic/blob/main/Docker/Dockerfile).

### Building the Docker Image

If you do not want to create a `Dockerfile` yourself, you can build an image based on our Docker example file. To do that, please run the following command in the root of the repository:

```sh
docker build -t mytoolit/icotronic -f Docker/Dockerfile .
```

### Using ICOtronic in the Docker Container

1. Run the container **(Terminal 1)**
   1. Open a new terminal window

   2. Open a shell in the Docker container

      ```sh
      docker run --rm -it --name icotronic mytoolit/icotronic
      ```

2. Move the CAN interface into the network space of the Docker container **(Terminal 2)**

   ```sh
   export DOCKERPID="$(docker inspect -f '{{ .State.Pid }}' icotronic)"
   sudo ip link set can0 netns "$DOCKERPID"
   sudo nsenter -t "$DOCKERPID" -n ip link set can0 type can bitrate 1000000
   sudo nsenter -t "$DOCKERPID" -n ip link set can0 up
   ```

   > **Note:** Alternatively you can also add the option `--network host` to the Docker command from step 1. Please check out the [Docker documentation](https://docs.docker.com/engine/network/drivers/host/) to learn more about the consequences of using this option.

3. Run a test command in Docker container **(Terminal 1)** e.g.:

   ```sh
   icon list
   ```
