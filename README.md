# Survey in a bottle

*Survey in a bottle* is a minimalistic web-application based on [flask](https://flask.palletsprojects.com/en/1.1.x/) and [surveyJS](https://surveyjs.io).
It runs stateless and stand-alone on your own computer or server. It does not use any non-free proprietary elements. It doesn't store any (meta-)data of participants apart for the answers of the survey.

```
 🍪  No cookies
 👀  No trackers
 💸  No vendor lock-in

 💫  Only surveys
```

## Usage

To create a survey, visit [the surveyJS creator](https://surveyjs.io/create-survey).
Once you are happy with the results, download the survey and save it as a `JSON` file.
After you installed *survey in a bottle* on your server, use the API to upload your survey.
You can use good old `curl` to do that.
From your command line simply run

```
curl https://survey.example.net/survey-name -H 'Authorization: Token YOUR_SECRET_GOES_HERE' -H "Content-Type: application/json" -X PUT --data @survey.json
```

The survey is now available at `https://survey.example.net/survey-name`.

You can upload as many surveys as you like but every survey needs a unique name (replace `survey-name` with something that makes sense to you).
If you need to edit the survey, just overwrite the existing one with the same command.

```
curl https://survey.example.net/survey-name -H 'Authorization: Token YOUR_SECRET_GOES_HERE' -H "Content-Type: application/json" -X PUT --data @survey.json
```

To get the survey results you can use `wget`:

```
wget https://survey.example.net/survey-name/results --header 'Authorization: Token YOUR_SECRET_GOES_HERE' -O results.tar.gz
```

The results are stored in your server's file system. By default they are stored in a temporary directory.
Every result is saved in a separate `.json` file.
The filename contains a UNIX time stamp of the moment the result was submitted.


## Run via Podman or Docker

```
podman volume create surveys
podman run -v surveys:/srv/surveys -e DATA_DIR=/srv/surveys -e AUTH_TOKEN=super_secret mswillus/survey-in-a-bottle
```


## Install via python-pip

If you just want to run the application:

```
pip install -r requirements.txt
export AUTH_TOKEN=super_secret
waitress-serve --call  app:app.create_app
```

### Configuration

The app can be configured via environment variables

| name | default | description |
|------|---------|-------------|
| AUTH_TOKEN |   | Password needed to change surveys and download results |
| DATA_DIR   | temp directory | Directory in which survey results will be stored |

### Dev environment

If you want to run a dev stack you probably want to use [direnv](https://direnv.net) and [nix](https://nixos.org/).
If not, make sure you use `python>=3.8` and `virtualenv`.

```
direnv allow          # assuming you use direnv and nix
pip install -r requirements.txt -r requirements-dev.txt
flask run
```

Run the tests with

```
pytest
ptw
```

And do not forget to enable pre-commit hooks before you commit!

```
pre-commit install
```

## Feature requests?

 This project is really just me scratching an itch but in case you want to use it but it lacks an essential feature which you really need, please do not hesitate to reach out!
