import asyncio
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

    async def extract_frame(
        self,
        source: Path,
        target: Path,
        at: float,
    ) -> None:
        """
        Сохраняет один кадр в PNG.
        """
        if at < 0:
            raise ValueError("Frame timestamp must be non-negative")

        await self._run(
            "-i",
            str(source),
            # "-ss",
            # str(at),
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            str(target),
        )

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
