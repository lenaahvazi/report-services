from apscheduler.schedulers.background import BackgroundScheduler
import cherrypy
import os
import time
import config
from helpers import prepareration_process, register


class SensorReportService(object):
    def __init__(self):
        self.last_call_time = 0

    @cherrypy.expose
    def download_report(self):
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time

        if time_since_last_call < 30:
            cherrypy.response.status = 429
            return "API can be called every 30 seconds. Please wait and try again."

        self.last_call_time = current_time

        # Generate the PDF report
        pdf_filename = prepareration_process(75599)

        if os.path.exists(pdf_filename):
            return cherrypy.lib.static.serve_file(pdf_filename, 'application/x-download', 'attachment',
                                                  os.path.basename(pdf_filename))
        return "Report not generated yet. Please try again.", 404


scheduler = BackgroundScheduler()

if __name__ == "__main__":
    register()

    interval = config.registerInterval
    scheduler.add_job(register, 'interval', seconds=interval)
    scheduler.start()

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 7020,
    })

    try:
        cherrypy.quickstart(SensorReportService(), '/api/v1')
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
