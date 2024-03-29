# NGDAC

This page is a collection of documents and resources describing the NetCDF file specification,
data provider registration and data set submission processes for contributing real-time and delayed-mode glider data sets to the U.S. IOOS National Glider Data Assembly Center (NGDAC).

See the website at https://ioos.github.io/glider-dac/

## Deploying site locally
Requirements:
* bundle
* Jekyll

See [IOOS How To: Local Development with Jekyll](https://ioos.github.io/ioos-documentation-jekyll-skeleton/howto.html#local-development-with-jekyll).

Clone this repository:
```commandline
git clone https://github.com/ioos/glider-dac.git
```
To build the site, in the `glider-dac/` directory run:
```commandline
bundle exec jekyll serve --config _config.yml --watch --verbose --incremental
```
This will deploy a website at: http://127.0.0.1:4000/glider-dac/

Make edits to the appropriate markdown files in `_docs/`. 

If changing headers and menus, stop the running server by entering `ctrl-c` in the terminal. Then run:
```commandline
bundle exec jekyll clean
```
Then build the site again.
```commandline
bundle exec jekyll serve --config _config.yml --watch --verbose --incremental
```
And review at http://127.0.0.1:4000/glider-dac/
