import uuid
import os

from pathlib import Path

from golem.core.fileencrypt import FileEncryptor
from golem.resource.dirmanager import DirManager
from golem.task.result.resultpackage import EncryptingPackager, \
    EncryptingTaskResultPackager, ExtractedPackage, ZipPackager, backup_rename
from golem.testutils import TempDirFixture


class PackageDirContentsFixture(TempDirFixture):

    def setUp(self):
        super().setUp()

        task_id = str(uuid.uuid4())
        dir_manager = DirManager(self.path)

        res_dir = dir_manager.get_task_temporary_dir(task_id)
        out_dir = os.path.join(res_dir, 'out_dir')
        out_dir_file = os.path.join(out_dir, 'dir_file')
        out_file = os.path.join(res_dir, 'out_file')

        os.makedirs(out_dir, exist_ok=True)

        with open(out_file, 'w') as f:
            f.write("File contents")
        with open(out_dir_file, 'w') as f:
            f.write("Dir file contents")

        self.dir_manager = dir_manager
        self.task_id = task_id
        self.secret = FileEncryptor.gen_secret(10, 20)

        self.disk_files = [out_file, out_dir_file]

        disk_file_names = [os.path.basename(f) for f in self.disk_files]
        self.all_files = disk_file_names

        self.res_dir = res_dir
        self.out_dir = out_dir
        self.out_path = os.path.join(self.out_dir, str(uuid.uuid4()))


class TestZipPackager(PackageDirContentsFixture):

    def testCreate(self):
        zp = ZipPackager()
        path, _ = zp.create(self.out_path, self.disk_files)

        self.assertTrue(os.path.exists(path))

    def testExtract(self):
        zp = ZipPackager()
        zp.create(self.out_path, self.disk_files)
        files, out_dir = zp.extract(self.out_path)

        self.assertEqual(len(files), len(self.all_files))


# pylint: disable=too-many-instance-attributes
class TestZipDirectoryPackager(TempDirFixture):
    def setUp(self):
        super().setUp()

        task_id = str(uuid.uuid4())
        dir_manager = DirManager(self.path)

        res_dir = dir_manager.get_task_temporary_dir(task_id)
        out_dir = os.path.join(res_dir, 'out_dir')

        os.makedirs(out_dir, exist_ok=True)

        self.dir_manager = dir_manager
        self.task_id = task_id
        self.secret = FileEncryptor.gen_secret(10, 20)

        # Create directory structure:
        #    |-- directory
        #    |-- directory2
        #    |   |-- directory3
        #    |   |   `-- file.txt
        #    |   `-- file.txt
        #    `-- file.txt

        file_path = os.path.join(res_dir, "file.txt")
        directory_path = os.path.join(res_dir, "directory")
        directory2_path = os.path.join(res_dir, "directory2/")
        directory2_file_path = os.path.join(directory2_path, "file.txt")
        directory3_path = os.path.join(directory2_path, "directory3/")
        directory3_file_path = os.path.join(directory3_path, "file.txt")

        os.makedirs(directory_path)
        os.makedirs(directory2_path)
        os.makedirs(directory3_path)
        with open(file_path, 'w') as out:
            out.write("content")
        with open(directory2_file_path, 'w') as out:
            out.write("content")
        with open(directory3_file_path, 'w') as out:
            out.write("content")

        self.disk_files = [
            file_path,
            directory_path,
            directory2_path,
        ]

        self.expected_results = [
            os.path.basename(file_path),
            os.path.basename(directory_path),
            os.path.relpath(directory2_path, res_dir),
            os.path.relpath(directory3_path, res_dir),
            os.path.relpath(directory2_file_path, res_dir),
            os.path.relpath(directory3_file_path, res_dir)
        ]

        self.res_dir = res_dir
        self.out_dir = out_dir
        self.out_path = os.path.join(self.out_dir, str(uuid.uuid4()))

    def testCreate(self):
        zp = ZipPackager()
        path, _ = zp.create(self.out_path, self.disk_files)

        self.assertTrue(os.path.exists(path))

    def testExtract(self):
        zp = ZipPackager()
        zp.create(self.out_path, self.disk_files)
        files, _ = zp.extract(self.out_path)
        files = [str(Path(f)) for f in files]
        self.assertTrue(set(files) == set(self.expected_results))


class TestEncryptingPackager(PackageDirContentsFixture):

    def testCreate(self):
        ep = EncryptingPackager(self.secret)
        path, _ = ep.create(self.out_path, self.disk_files)

        self.assertTrue(os.path.exists(path))

    def testExtract(self):
        ep = EncryptingPackager(self.secret)
        ep.create(self.out_path, self.disk_files)
        files, _ = ep.extract(self.out_path)

        self.assertTrue(len(files) == len(self.all_files))


class TestEncryptingTaskResultPackager(PackageDirContentsFixture):

    def testCreate(self):
        etp = EncryptingTaskResultPackager(self.secret)

        path, _ = etp.create(self.out_path,
                             disk_files=self.disk_files)

        self.assertTrue(os.path.exists(path))

    def testExtract(self):
        etp = EncryptingTaskResultPackager(self.secret)

        path, _ = etp.create(self.out_path,
                             disk_files=self.disk_files)

        extracted = etp.extract(path)

        self.assertIsInstance(extracted, ExtractedPackage)
        self.assertEqual(len(extracted.files), len(self.all_files))


class TestExtractedPackage(PackageDirContentsFixture):

    def testToExtraData(self):
        etp = EncryptingTaskResultPackager(self.secret)

        path, _ = etp.create(self.out_path,
                             disk_files=self.disk_files)

        extracted = etp.extract(path)
        full_path_files = extracted.get_full_path_files()

        self.assertEqual(len(full_path_files), len(self.all_files))

        for filename in full_path_files:
            self.assertTrue(os.path.exists(filename))


class TestBackupRename(TempDirFixture):

    FILE_CONTENTS = 'Test file contents'

    def test(self):
        file_dir = os.path.join(self.path, 'directory')
        file_path = os.path.join(file_dir, 'file')
        os.makedirs(file_dir, exist_ok=True)

        def create_file():
            with open(file_path, 'w') as f:
                f.write(self.FILE_CONTENTS)

        def file_count():
            return len(os.listdir(file_dir))

        def file_contents(num):
            with open(file_path + '.{}'.format(num)) as f:
                return f.read().strip()

        backup_rename(file_path)
        assert file_count() == 0

        create_file()

        assert file_count() == 1
        backup_rename(file_path, max_iterations=2)
        assert file_count() == 1
        assert file_contents(1) == self.FILE_CONTENTS

        create_file()

        backup_rename(file_path, max_iterations=2)
        assert file_count() == 2
        assert file_contents(1) == self.FILE_CONTENTS
        assert file_contents(2) == self.FILE_CONTENTS

        create_file()

        backup_rename(file_path, max_iterations=2)
        assert file_count() == 3

        files = os.listdir(file_dir)
        files.remove('file.1')
        files.remove('file.2')

        with open(os.path.join(file_dir, files[0])) as f:
            assert f.read().strip() == self.FILE_CONTENTS
