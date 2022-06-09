from os import listdir, remove
from os.path import join
from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.joern.v040 import JoernProcessing
from bugfinder.settings import ROOT_DIR
from tests import patch_paths


class TestJoernDatasetProcessingConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.processing.joern.AbstractJoernProcessing.configure_container",
                "bugfinder.processing.joern.v040.LOGGER",
                "bugfinder.base.processing.LOGGER",
            ],
        )

        self.dataset_processing = JoernProcessing(None)

    def test_image_name_is_correct(self):
        expected_image_name = "joern-lite:0.4.0"

        self.dataset_processing.configure_container()

        self.assertEqual(self.dataset_processing.image_name, expected_image_name)

    def test_container_name_is_correct(self):
        expected_container_name = "joern040"

        self.dataset_processing.configure_container()

        self.assertEqual(
            self.dataset_processing.container_name, expected_container_name
        )


class TestJoernDatasetProcessingSendCommands(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.processing.joern.v040.LOGGER",
                "bugfinder.base.processing.LOGGER",
            ],
        )

        self.dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset.joern_dir = join(
            ROOT_DIR, "tests", "fixtures", "dataset04", "joern.db"
        )
        self.dataset_processing = JoernProcessing(self.dataset)

    def tearDown(self) -> None:
        import_dir = join(self.dataset.joern_dir, "import")
        for filename in listdir(import_dir):
            if filename == ".keep":
                continue

            remove(join(import_dir, filename))

    @patch("bugfinder.processing.joern.v040.exists")
    @patch("bugfinder.processing.joern.v040.open")
    @patch("bugfinder.processing.joern.v040.makedirs")
    def test_create_output_path_if_it_does_not_exist(
        self, mock_makedirs, mock_open, mock_exists
    ):
        mock_makedirs.return_value = None
        mock_exists.return_value = False
        self.dataset_processing.send_commands()

        self.assertTrue(mock_makedirs.called)

    @patch("bugfinder.processing.joern.v040.exists")
    def test_output_file_names_correct(self, mock_exists):
        mock_exists.return_value = True
        self.dataset_processing.send_commands()

        self.assertListEqual(
            [
                filename
                for filename in listdir(join(self.dataset.joern_dir, "import"))
                if filename != ".keep"
            ],
            listdir(join(self.dataset.joern_dir, "import.expected")),
        )

    @patch("bugfinder.processing.joern.v040.exists")
    def test_output_file_contents_correct(self, mock_exists):
        mock_exists.return_value = True
        self.dataset_processing.send_commands()

        for filename in listdir(join(self.dataset.joern_dir, "import.expected")):
            with open(join(self.dataset.joern_dir, "import", filename)) as fp:
                returned_content = fp.read()

            with open(join(self.dataset.joern_dir, "import.expected", filename)) as fp:
                expected_content = fp.read()

            self.assertEqual(returned_content, expected_content)
