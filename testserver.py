###############################################################################
# Script to create a simple Flask web server
#

from flask import Flask, jsonify, request, make_response, Response, abort
import signal
import sys
import argparse

app = Flask(__name__)

count = 0
users = 0

###############################################################################
class ErrorCode(object):
    emptyCommandLineParameters = 100


###############################################################################
def signal_handler(sig, frame):
    if sig == signal.SIGINT:
        print('----- Ctrl-C is pressed -----')
        sys.exit(0)


###############################################################################
# MAIN
#
def main(argv):
    signal.signal(signal.SIGINT, signal_handler)

    args = argparse.ArgumentParser(description='Load Test Sample Flask Server')
    args.add_argument('--port', "-p", type=int, action="store", dest="port_number", default=5555,
                      help="The port number to be used by the web server.")
    args.add_argument('--debug_mode', "-d", action="store_true", dest="debug_mode", default=False,
                      help="Enable debug mode? Default is false.")

    if len(argv) == 1:
        args.print_help()
        return ErrorCode.emptyCommandLineParameters

    given_args = args.parse_args()
    port_number = given_args.port_number
    debug_mode = given_args.debug_mode

    print('\nRunning Flask Web Service on localhost:{}\t\tDebug mode={}\n\n'.format(port_number, debug_mode))
    app.run(port=port_number, debug=debug_mode)


###############################################################################
# REST API handling
#

@app.route('/test/version', methods=['GET'])
def getVersion():
    global users, count
    return jsonify({'name': 'dummy server', 'version': '0.1', 'users': users, 'count': count})


###############################################################################
@app.route('/test/update', methods=['POST'])
def update_entry():
    global count
    '''data = request.get_json(force=True)
    if not data:
        abort(401)'''
    count += 1
    return Response(status=200, mimetype='application/json')


###############################################################################
@app.route('/test/count', methods=['GET'])
def query_entry():
    global count
    return jsonify({'count': count}), 200


###############################################################################
@app.route('/login', methods=['GET'])
def login():
    global users
    users += 1
    return Response(status=200, mimetype='application/json')


###############################################################################
@app.route('/logout', methods=['GET'])
def logout():
    global users
    users -= 1
    return Response(status=200, mimetype='application/json')


###############################################################################
# Flask will generate one HTML payload and send back to API caller by defult,
# which is NOT what we want here, so comes this error handler.
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


###############################################################################
if __name__ == '__main__':
    sys.exit(main(sys.argv))
