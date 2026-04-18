import unittest
from unittest.mock import MagicMock, call, patch

import config
from services import jobs


class JobSchedulerRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.original_scheduler = jobs.scheduler
        self.original_daily_hour = config.settings.daily_research_hour_utc
        self.original_interval = config.settings.pre_close_check_interval_hours
        jobs.scheduler = None

    def tearDown(self):
        jobs.scheduler = self.original_scheduler
        config.settings.daily_research_hour_utc = self.original_daily_hour
        config.settings.pre_close_check_interval_hours = self.original_interval

    def test_start_scheduler_registers_expected_jobs_and_cadence(self):
        config.settings.daily_research_hour_utc = 22
        config.settings.pre_close_check_interval_hours = 6

        scheduler_mock = MagicMock()

        with patch("services.jobs.BackgroundScheduler", return_value=scheduler_mock) as mock_scheduler_cls, patch(
            "services.jobs.CronTrigger", side_effect=["daily_cron", "digest_cron"]
        ) as mock_cron, patch("services.jobs.IntervalTrigger", return_value="preclose_interval") as mock_interval:
            jobs.start_scheduler()

        mock_scheduler_cls.assert_called_once_with(timezone="UTC")
        mock_cron.assert_has_calls([call(hour=22, minute=0), call(hour=23, minute=0)])
        mock_interval.assert_called_once_with(hours=6)

        self.assertEqual(
            scheduler_mock.add_job.call_args_list,
            [
                call(
                    jobs.safe_daily_research_job,
                    "daily_cron",
                    id="daily_research",
                    replace_existing=True,
                ),
                call(
                    jobs.safe_preclose_monitor_job,
                    "preclose_interval",
                    id="preclose_monitor",
                    replace_existing=True,
                ),
                call(
                    jobs.safe_send_daily_digest_job,
                    "digest_cron",
                    id="daily_digest",
                    replace_existing=True,
                ),
            ],
        )
        scheduler_mock.start.assert_called_once_with()
        self.assertIs(jobs.scheduler, scheduler_mock)

    def test_start_scheduler_is_noop_when_scheduler_exists(self):
        existing_scheduler = MagicMock()
        jobs.scheduler = existing_scheduler

        with patch("services.jobs.BackgroundScheduler") as mock_scheduler_cls:
            jobs.start_scheduler()

        mock_scheduler_cls.assert_not_called()
        self.assertIs(jobs.scheduler, existing_scheduler)


if __name__ == "__main__":
    unittest.main()
