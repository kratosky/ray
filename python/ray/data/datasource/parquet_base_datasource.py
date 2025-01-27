import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from ray.data.block import BlockAccessor
from ray.data.datasource.file_based_datasource import (
    FileBasedDatasource,
    _resolve_kwargs,
)
from ray.util.annotations import PublicAPI

if TYPE_CHECKING:
    import pyarrow


logger = logging.getLogger(__name__)


@PublicAPI
class ParquetBaseDatasource(FileBasedDatasource):
    """Minimal Parquet datasource, for reading and writing Parquet files."""

    _FILE_EXTENSION = "parquet"

    def __init__(
        self,
        paths: Union[str, List[str]],
        read_table_args: Optional[Dict[str, Any]] = None,
        **file_based_datasource_kwargs,
    ):
        super().__init__(paths, **file_based_datasource_kwargs)

        if read_table_args is None:
            read_table_args = {}

        self.read_table_args = read_table_args

    def get_name(self):
        """Return a human-readable name for this datasource.
        This will be used as the names of the read tasks.
        Note: overrides the base `FileBasedDatasource` method.
        """
        return "ParquetBulk"

    def _read_file(self, f: "pyarrow.NativeFile", path: str):
        import pyarrow.parquet as pq

        use_threads = self.read_table_args.pop("use_threads", False)
        return pq.read_table(f, use_threads=use_threads, **self.read_table_args)

    def _open_input_source(
        self,
        filesystem: "pyarrow.fs.FileSystem",
        path: str,
        **open_args,
    ) -> "pyarrow.NativeFile":
        # Parquet requires `open_input_file` due to random access reads
        return filesystem.open_input_file(path, **open_args)

    def _write_block(
        self,
        f: "pyarrow.NativeFile",
        block: BlockAccessor,
        writer_args_fn: Callable[[], Dict[str, Any]] = lambda: {},
        **writer_args,
    ):
        import pyarrow.parquet as pq

        writer_args = _resolve_kwargs(writer_args_fn, **writer_args)
        pq.write_table(block.to_arrow(), f, **writer_args)
