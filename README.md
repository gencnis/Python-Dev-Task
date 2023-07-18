# Interpol Data Project

## Table of Contents
- [Introduction](#introduction)
- [Containers](#containers)
  - [Container A](#container-a)
  - [Container B](#container-b)
  - [Container C](#container-c)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction<a name="introduction"></a>
This project involves extracting and filterin data from Interpol using Docker Compose.

## Containers<a name="containers"></a>

### Container A<a name="container-a"></a>
Container A retrieves the red list data published by Interpol. The data is then transferred to the message queue system in Container C.
Container A includes:
- Python 3.x
- BeautifulSoup
- Requests
- pika

### Container B<a name="container-b"></a>
Container B is a Python-based web server. It listens to the message queue in Container C. The information obtained from the queue is stored in the desired database. These details are displayed on a simple HTML web page provided by the web server. The web page should be updated whenever new information is obtained from the queue. 
Container B includes:
- Python 3.x
- Flask
- Flask-SQLAlchemy
- Requests
- pika

### Container C<a name="container-c"></a>
Container C hosts a message queue system called RabbitMQ.
Container C includes:
- Python 3.x
- RabbitMQ

## Dependencies<a name="dependencies"></a>
- Docker
- Docker Compose

## Usage<a name="usage"></a>
1. Install Docker and Docker Compose.
2. Clone this repository.
3. Navigate to the project directory.
4. Run the following command to start the containers: `docker-compose up --build`.
5. Access the web server's interface by visiting the appropriate URL in your browser.

## Contributing<a name="contributing"></a>
Contributions are welcome! If you have any suggestions, ideas, or bug reports, please open an issue or submit a pull request.

## License<a name="license"></a>
This project is licensed under the [MIT License](LICENSE).
