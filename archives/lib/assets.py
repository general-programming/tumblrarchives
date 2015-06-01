from flask.ext.assets import Environment, Bundle

assets = Environment()

js = Bundle('js/jquery.min.js', 'js/bootstrap.min.js', filters='jsmin', output='js/packed.js')
css = Bundle('css/bootstrap.min.css', 'css/font-awesome.min.css', 'css/main.css', filters='cssmin', output='css/packed.css')

assets.register('js_all', js)
assets.register('css_all', css)
