# reimagined-spork

[![Build Status](https://travis-ci.org/EduBergantini/reimagined-spork.svg?branch=master)](https://travis-ci.org/EduBergantini/reimagined-spork)

## Instalation
Use Docker Compose to install the app
```bash
docker-compose build
```

## Tests
Execute the following command
```bash
docker-compose --rm run app sh -c "python manage.py test && flake8"
```

## Execution
Execute the following command
```bash
docker-compose up
```
## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
