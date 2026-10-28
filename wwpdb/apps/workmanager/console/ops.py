##
# File:  ops.py
# Date:  28-Oct-2026
##
"""JSON request handlers for /service/workmanager/console_*."""

import sys
import traceback

from wwpdb.apps.workmanager.console import actions, auth, catalog, jobs
from wwpdb.apps.workmanager.db_access.StatusDbApi import StatusDbApi
from wwpdb.utils.session.WebRequest import ResponseContent


class ConsoleOps(object):
    def __init__(self, reqObj, session_id, session_path, site_id, verbose=False, log=sys.stderr):
        self.__reqObj = reqObj
        self.__sessionId = session_id
        self.__sessionPath = session_path
        self.__siteId = site_id
        self.__verbose = verbose
        self.__lfh = log

    def _json(self, payload=None, error=None):
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        data = payload if payload is not None else {}
        data["sessionid"] = self.__sessionId
        if error:
            rC.setError(errMsg=str(error))
            data["errorflag"] = True
            data["errortext"] = str(error)
        else:
            data["errorflag"] = False
        rC.addDictionaryItems(data)
        return rC

    def login(self):
        username = str(self.__reqObj.getValue("username") or "").strip()
        password = str(self.__reqObj.getValue("password") or "")
        if not username or not password:
            return self._json(error="Enter your Work Manager username and password.")
        db = StatusDbApi(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        user_info = db.Autenticate(username, password)
        if not user_info:
            return self._json(error="Invalid login.")
        if not auth.group_allowed(user_info):
            return self._json(error="This page is for annotators (ANN / LANN).")
        stored = auth.write_auth(self.__sessionPath, user_info)
        return self._json(
            {
                "annotator": stored["annotator"],
                "first_name": stored["first_name"],
                "last_name": stored["last_name"],
                "group_code": stored["group_code"],
                "group_name": stored["group_name"],
            }
        )

    def logout(self):
        auth.clear_auth(self.__sessionPath)
        return self._json({"ok": True})

    def whoami(self):
        try:
            user = auth.require_console_user(self.__sessionPath, self.__reqObj.getValue("annotator"))
        except ValueError as exc:
            return self._json(error=str(exc))
        return self._json(
            {
                "annotator": user["annotator"],
                "first_name": user.get("first_name") or "",
                "last_name": user.get("last_name") or "",
                "group_code": user.get("group_code") or "",
                "group_name": user.get("group_name") or "",
            }
        )

    def start(self):
        try:
            user = auth.require_console_user(self.__sessionPath, self.__reqObj.getValue("annotator"))
        except ValueError as exc:
            return self._json(error=str(exc))
        action_id = str(self.__reqObj.getValue("action_id") or "").strip()
        if action_id not in catalog.IMPLEMENTED_ACTION_IDS:
            return self._json(error="Unknown or not-yet-implemented action.")
        deposition_ids = jobs.parse_deposition_ids(self.__reqObj.getValue("deposition_ids"))
        if not deposition_ids:
            return self._json(error="No valid deposition IDs (expected D_1234567890).")
        extra = {}
        if action_id == catalog.ACTION_RUN_OR_RESTART_LEVEL2_MODULE:
            try:
                module_row, operation = catalog.validate_level2_choice(
                    self.__reqObj.getValue("level2_module"),
                    self.__reqObj.getValue("level2_operation"),
                )
            except ValueError as exc:
                return self._json(error=str(exc))
            extra["level2_module"] = module_row["id"]
            extra["level2_operation"] = operation
            extra["level2_label"] = module_row["label"]
        annotator = user["annotator"]
        progress = jobs.new_job(self.__sessionPath, action_id, annotator, deposition_ids, extra=extra)
        job_id = progress["job_id"]
        jobs.append_log(self.__sessionPath, job_id, "Started %s as %s (%s IDs)" % (catalog.action_label(action_id), annotator, len(deposition_ids)))
        cancelled = False
        for dep_id in deposition_ids:
            if jobs.cancel_requested(self.__sessionPath, job_id):
                cancelled = True
                jobs.append_log(self.__sessionPath, job_id, "Cancel requested; remaining IDs skipped.")
                break
            jobs.set_row(self.__sessionPath, job_id, dep_id, "running")
            jobs.append_log(self.__sessionPath, job_id, "[%s] running" % dep_id)
            try:
                detail = actions.run_action(
                    self.__siteId,
                    action_id,
                    dep_id,
                    annotator,
                    extra,
                    verbose=self.__verbose,
                    log=self.__lfh,
                )
                jobs.set_row(self.__sessionPath, job_id, dep_id, "ok", "")
                jobs.append_log(self.__sessionPath, job_id, "[%s] OK %s" % (dep_id, detail))
            except Exception as exc:  # noqa: BLE001
                traceback.print_exc(file=self.__lfh)
                err = str(exc) or "Action failed."
                jobs.set_row(self.__sessionPath, job_id, dep_id, "failed", err)
                jobs.append_log(self.__sessionPath, job_id, "[%s] FAILED %s" % (dep_id, err))
        if cancelled:
            jobs.finish_job(self.__sessionPath, job_id, status="done", error="Cancelled.")
        else:
            jobs.finish_job(self.__sessionPath, job_id, status="done")
        return self._json(jobs.load_progress(self.__sessionPath, job_id))

    def status(self):
        try:
            auth.require_console_user(self.__sessionPath, self.__reqObj.getValue("annotator"))
        except ValueError as exc:
            return self._json(error=str(exc))
        job_id = str(self.__reqObj.getValue("job_id") or "").strip()
        progress = jobs.load_progress(self.__sessionPath, job_id)
        if not progress:
            return self._json(error="Job not found.")
        return self._json(progress)

    def cancel(self):
        try:
            auth.require_console_user(self.__sessionPath, self.__reqObj.getValue("annotator"))
        except ValueError as exc:
            return self._json(error=str(exc))
        job_id = str(self.__reqObj.getValue("job_id") or "").strip()
        if not jobs.request_cancel(self.__sessionPath, job_id):
            return self._json(error="Job not found.")
        return self._json({"ok": True, "job_id": job_id})
