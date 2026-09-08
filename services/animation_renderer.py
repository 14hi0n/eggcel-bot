import asyncio
import json
from contextlib import suppress
from pathlib import Path


class AnimationRenderer:
    def __init__(
        self,
        ffmpeg_path: str = "ffmpeg",
        timeout: float = 90,
        max_parallel: int = 2,
    ) -> None:
        if timeout <= 0 or max_parallel < 1:
            raise ValueError("Timeout and max_parallel must be positive")

        self._ffmpeg_path = ffmpeg_path
        self._timeout = timeout
        self._semaphore = asyncio.Semaphore(max_parallel)

    async def extract_middle_frame(self, source: Path, target: Path) -> None:
        """Сохраняет средний по номеру кадр анимации в PNG."""
        async with self._semaphore:
            process = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-count_frames",
                "-show_entries",
                "stream=nb_read_frames",
                "-of",
                "json",
                str(source),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            communication = asyncio.create_task(process.communicate())
            try:
                stdout, stderr = await asyncio.wait_for(
                    asyncio.shield(communication), timeout=self._timeout
                )
            except TimeoutError, asyncio.CancelledError:
                with suppress(ProcessLookupError):
                    process.kill()
                await communication
                raise

        if process.returncode != 0:
            details = stderr.decode(errors="replace")[-2000:]
            raise RuntimeError(f"FFprobe failed: {details}")

        try:
            info = json.loads(stdout)
            frame_count = int(info["streams"][0]["nb_read_frames"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError("Could not determine video frame count") from exc

        if frame_count < 1:
            raise RuntimeError("Animation contains no video frames")

        frame_index = frame_count // 2
        await self._run(
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-vf",
            f"select=eq(n\\,{frame_index})",
            "-frames:v",
            "1",
            "-fps_mode",
            "vfr",
            str(target),
        )

        if not target.is_file() or target.stat().st_size == 0:
            raise RuntimeError("FFmpeg did not produce a preview frame")

    async def render(
        self,
        source: Path,
        overlay: Path,
        target: Path,
    ) -> None:
        """
        Накладывает прозрачный PNG на всю анимацию и сохраняет в MP4 без звука.
        """
        # боже как страшно
        await self._run(
            "-i",
            str(source),
            "-i",
            str(overlay),
            "-filter_complex",
            "[0:v:0]setpts=PTS-STARTPTS[v];"
            "[v][1:v:0]overlay=0:0:eof_action=repeat:repeatlast=1,"
            "pad=ceil(iw/2)*2:ceil(ih/2)*2,setsar=1[out]",
            "-map",
            "[out]",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-movflags",
            "+faststart",
            str(target),
        )

    async def _run(self, *args: str) -> None:
        async with self._semaphore:
            process = await asyncio.create_subprocess_exec(
                self._ffmpeg_path,
                "-nostdin",
                "-y",
                "-v",
                "error",
                *args,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )

            communication = asyncio.create_task(process.communicate())

            try:
                _, stderr = await asyncio.wait_for(
                    asyncio.shield(communication), timeout=self._timeout
                )
            except TimeoutError, asyncio.CancelledError:
                with suppress(ProcessLookupError):
                    process.kill()

                await communication
                raise

            if process.returncode != 0:
                details = stderr.decode(errors="replace")[-2000:]
                raise RuntimeError(f"FFmpeg failed: {details}")
