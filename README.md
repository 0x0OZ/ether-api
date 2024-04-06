# Blockchain Networks universal API

## What is this?

This api lets you interact with different blockchain networks and different explorers in a unified way. It is a wrapper around different blockchain explorers and networks, so you can interact with them in a unified way. It is easy to use and easy to extend.

## How to use it?

After running the server, 

you can access the api at `http://localhost:5000/docs`. This will show you the swagger documentation, where you can see all the available endpoints and try them out.

## How to run it?

Copy the `.env.example` file to `.env` and fill in the required values. Then run the following command:
```bash
gunicorn main:app -b :80
```

[Demo Video](https://github.com/0x0OZ/ether-api/assets/52073989/236cc703-6a53-450a-9d76-ce35c969ad22)


## How to extend it?

You can extend the api by adding new networks and explorers in `config/networks/` and `config/apis/` which you can know how to do by looking at the existing ones. 

## Notes for developers

These notes provide information about the placeholders used in the code which you will see when requesting the api docs:

- `${...}` is a placeholder for config vars. Those are pulled from the `config/networks/*` files

- `$[...]` is a placeholder for api params. Those are pulled from the request query params `?...`

- `<%...%>` is a placeholder for api post params. Those are not pulled but rather converted to POST params in the request body

Make sure to replace the placeholders with the appropriate values or variables when using the API.
