
if __name__ == "__main__":
	import runStatus
	runStatus.preloadDicts = False

import logging
import psycopg2
import functools
import abc

import threading
import settings
import os
import traceback
import contextlib


from sqlalchemy import or_

import nameTools as nt
import MangaCMS.db as mdb
import MangaCMS.lib.LogMixin
import MangaCMS.lib.MonitorMixin

class MangaScraperDbBase(MangaCMS.lib.LogMixin.LoggerMixin, MangaCMS.lib.MonitorMixin.MonitorMixin):


	@abc.abstractmethod
	def plugin_name(self):
		return None

	@abc.abstractmethod
	def plugin_key(self):
		return None

	@abc.abstractmethod
	def is_manga(self):
		return None

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.db = mdb

		if self.is_manga:
			self.shouldCanonize = True
			self.target_table = self.db.MangaReleases
		else:
			self.shouldCanonize = False
			self.target_table = self.db.HentaiReleases


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Misc Utilities
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	@contextlib.contextmanager
	def row_context(self, *args, **kwargs):
		with self.row_sess_context(*args, **kwargs) as row_tup:
			row, _ = row_tup
			yield row

	@contextlib.contextmanager
	def row_sess_context(self, dbid=None, url=None, limit_by_plugin=True, commit=True):

		assert url or dbid

		with self.db.session_context(commit=commit) as sess:
			row_q = sess.query(self.target_table)

			if limit_by_plugin:
				row_q = row_q.filter(self.target_table.source_site == self.plugin_key)

			if url:
				row_q = row_q.filter(self.target_table.source_id == url)
			elif dbid:
				row_q = row_q.filter(self.target_table.id == dbid)
			else:
				raise RuntimeError("How did this get executed?")

			yield (row_q.scalar(), sess)

	def _resetStuckItems(self):
		self.log.info("Resetting stuck downloads in DB")

		with self.db.session_context() as sess:
			res = sess.query(self.target_table)                         \
				.filter(self.target_table.source_site == self.plugin_key) \
				.filter(or_(
					self.target_table.state == 'fetching',
					self.target_table.state == 'processing',
					self.target_table.state == 'missing',
					))                                                  \
				.update({"state" : 'new'})
			self.log.info("Reset updated %s rows!", res)

		self.log.info("Download reset complete")

	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Tools
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
	import settings
	class TestClass(MangaScraperDbBase):


		plugin_name = "Wat?"
		logger_path = "Wat?"
		plugin_key = "mk"
		is_manga = True
		def go(self):
			print("Go?")

		def test(self):
			print("Wat?")


	import utilities.testBase as tb

	with tb.testSetup(load=False):
		obj = TestClass()
		print(obj)
		obj.test()
		obj._resetStuckItems()


