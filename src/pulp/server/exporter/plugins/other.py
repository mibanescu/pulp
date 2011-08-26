# -*- coding: utf-8 -*-
#
# Copyright © 2011 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
import os
import shutil
import pulp.server.util
from pulp.server.exporter.base import BaseExporter
from pulp.server.exporter.logutil import getLogger

log = getLogger(__name__)

class OtherExporter(BaseExporter):
    """
     other exporter plugin to export repository's custom metadata from pulp to target directory
    """
    def __init__(self, repoid, target_dir="./", start_date=None, end_date=None):
        """
        initialize other metadata exporter
        @param repoid: repository Id
        @type repoid: string
        @param target_dir: target directory where exported content is written
        @type target_dir: string
        @param start_date: optional start date from which the content needs to be exported
        @type start_date: date
        @param end_date: optional end date from which the content needs to be exported
        @type end_date: date
        """
        BaseExporter.__init__(self, repoid, target_dir, start_date, end_date)

    def export(self):
        """
        Export cutom metadata associated to the repository
        and metadata is updated with new custom file.
        """
        self.validate_target_path()
        repo = self.get_repository()
        self.progress['step'] = 'Exporting Custom Metadata'
        repo_path = "%s/%s/" % (pulp.server.util.top_repos_location(), repo['relative_path'])
        src_repodata_file = os.path.join(repo_path, "repodata/repomd.xml")
        src_repodata_dir  = os.path.dirname(src_repodata_file)
        tgt_repodata_dir  = os.path.join(self.target_dir, 'repodata')
        ftypes = pulp.server.util.get_repomd_filetypes(src_repodata_file)
        base_ftypes = ['primary', 'primary_db', 'filelists_db', 'filelists', 'other', 'other_db', 'updateinfo', 'comps']
        for ftype in ftypes:
            if ftype in base_ftypes:
                # no need to process these again
                continue
            filetype_path = os.path.join(src_repodata_dir, os.path.basename(pulp.server.util.get_repomd_filetype_path(src_repodata_file, ftype)))
            # modifyrepo uses filename as mdtype, rename to type.<ext>
            renamed_filetype_path = os.path.join(tgt_repodata_dir, \
                                         ftype + '.' + '.'.join(os.path.basename(filetype_path).split('.')[1:]))
            shutil.copy(filetype_path,  renamed_filetype_path)
            if os.path.isfile(renamed_filetype_path):
                log.info("Modifying repo for %s metadata" % ftype)
                pulp.server.util.modify_repo(tgt_repodata_dir, renamed_filetype_path)

    def get_progress(self):
        return self.print_progress(self.progress)