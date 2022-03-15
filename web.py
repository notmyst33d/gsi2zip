#!/usr/bin/env python3
import os, uuid, tempfile, shutil, asyncio, functools
from aiohttp import web
from subprocess import Popen, PIPE, call

formats = {
    "sparse": "Android sparse image",
    "raw": "Linux rev 1.0 ext2 filesystem data",
    "xz": "XZ compressed data",
    "gz": "gzip compressed data"
}

nested_formats = {
    "sparse": "Android sparse image",
    "raw": "Linux rev 1.0 ext2 filesystem data"
}

state = {}

cors = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*"
}

routes = web.RouteTableDef()

with open("index.html", "rb") as f:
    index_html = f.read()

async def async_call(loop, args, stdout=PIPE, shell=True):
    return await loop.run_in_executor(None, functools.partial(call, args, stdout=stdout, shell=shell))

async def async_Popen(loop, args, stdout=PIPE):
    return await loop.run_in_executor(None, functools.partial(Popen, args, stdout=stdout))

async def async_communicate(loop, p):
    return await loop.run_in_executor(None, p.communicate)

async def process_gsi(gsi_dir, gsi_file, gsi_format, gsi_arch, request_uuid):
    loop = asyncio.get_running_loop()

    state[request_uuid] = {}
    state[request_uuid]["finished"] = False
    state[request_uuid]["error"] = False
    state[request_uuid]["log"] = ""
    state[request_uuid]["log"] += f"Received request {request_uuid}\n"
    state[request_uuid]["log"] += f"Received arguments: {gsi_dir}, {gsi_file}, {gsi_format}, {gsi_arch}, {request_uuid}\n"

    shutil.copytree(f"template_{gsi_arch}", f"{gsi_dir}/template")

    if gsi_format == "sparse":
        state[request_uuid]["log"] += f"GSI already in sparse format\n"
    elif gsi_format == "raw":
        state[request_uuid]["log"] += f"GSI is in raw format, converting to sparse format\n"
        shutil.move(f"{gsi_dir}/{gsi_file}", f"{gsi_dir}/{gsi_file}.raw")
        p = await async_Popen(loop, ["./simg/img2simg", f"{gsi_dir}/{gsi_file}.raw", f"{gsi_dir}/{gsi_file}"])
        await async_communicate(loop, p)

        if p.returncode != 0:
            state[request_uuid]["log"] += f"img2simg returned {p.return_code}\n"
            state[request_uuid]["error"] = True
            shutil.rmtree(gsi_dir)
            await asyncio.sleep(3)
            return

        state[request_uuid]["log"] += f"Deleting unsparsed GSI\n"
        os.remove(f"{gsi_dir}/{gsi_file}.raw")
    elif gsi_format == "xz":
        state[request_uuid]["log"] += f"GSI is compressed using xz, uncompressing\n"
        p = await async_Popen(loop, ["unxz", "-T", "0", f"{gsi_dir}/{gsi_file}"])
        await async_communicate(loop, p)

        if p.returncode != 0:
            state[request_uuid]["log"] += f"xz returned {p.returncode}\n"
            state[request_uuid]["error"] = True
            shutil.rmtree(gsi_dir)
            await asyncio.sleep(3)
            return

        gsi_file = gsi_file.replace(".xz", "")
        gsi_format = None

        p = await async_Popen(loop, ["file", f"{gsi_dir}/{gsi_file}"])
        stdout, stderr = await async_communicate(loop, p)
        stdout = stdout.decode()

        if p.returncode != 0:
            state[request_uuid]["log"] += f"file returned {p.returncode}\n"
            state[request_uuid]["error"] = True
            shutil.rmtree(gsi_dir)
            await asyncio.sleep(3)
            return

        for k, v in nested_formats.items():
            if v in stdout:
                gsi_format = k

        if not gsi_format:
            state[request_uuid]["log"] += f"Unsupported nested format?\n"
            state[request_uuid]["error"] = True
            shutil.rmtree(gsi_dir)
            await asyncio.sleep(3)
            return

        if gsi_format == "sparse":
            state[request_uuid]["log"] += f"GSI already in sparse format\n"
        elif gsi_format == "raw":
            state[request_uuid]["log"] += f"GSI is in raw format, converting to sparse format\n"
            shutil.move(f"{gsi_dir}/{gsi_file}", f"{gsi_dir}/{gsi_file}.raw")
            p = await async_Popen(loop, ["./simg/img2simg", f"{gsi_dir}/{gsi_file}.raw", f"{gsi_dir}/{gsi_file}"])
            await async_communicate(loop, p)

            if p.returncode != 0:
                state[request_uuid]["log"] += f"img2simg returned {p.return_code}\n"
                state[request_uuid]["error"] = True
                shutil.rmtree(gsi_dir)
                await asyncio.sleep(3)
                return

            state[request_uuid]["log"] += f"Deleting unsparsed GSI\n"
            os.remove(f"{gsi_dir}/{gsi_file}.raw")
    elif gsi_format == "gz":
        state[request_uuid]["log"] += f"GSI is compressed using gz, uncompressing\n"
        p = await async_Popen(loop, ["gunzip", f"{gsi_dir}/{gsi_file}"])
        await async_communicate(loop, p)

        if p.returncode != 0:
            state[request_uuid]["log"] += f"gunzip returned {p.returncode}\n"
            state[request_uuid]["error"] = True
            shutil.rmtree(gsi_dir)
            await asyncio.sleep(3)
            return

        gsi_file = gsi_file.replace(".gz", "")
        gsi_format = None

        p = await async_Popen(loop, ["file", f"{gsi_dir}/{gsi_file}"])
        stdout, stderr = await async_communicate(loop, p)
        stdout = stdout.decode()

        if p.returncode != 0:
            state[request_uuid]["log"] += f"file returned {p.returncode}\n"
            state[request_uuid]["error"] = True
            shutil.rmtree(gsi_dir)
            await asyncio.sleep(3)
            return

        for k, v in nested_formats.items():
            if v in stdout:
                gsi_format = k

        if not gsi_format:
            state[request_uuid]["log"] += f"Unsupported nested format?\n"
            state[request_uuid]["error"] = True
            shutil.rmtree(gsi_dir)
            await asyncio.sleep(3)
            return

        if gsi_format == "sparse":
            state[request_uuid]["log"] += f"GSI already in sparse format\n"
        elif gsi_format == "raw":
            state[request_uuid]["log"] += f"GSI is in raw format, converting to sparse format\n"
            shutil.move(f"{gsi_dir}/{gsi_file}", f"{gsi_dir}/{gsi_file}.raw")
            p = await async_Popen(loop, ["./simg/img2simg", f"{gsi_dir}/{gsi_file}.raw", f"{gsi_dir}/{gsi_file}"])
            await async_communicate(loop, p)

            if p.returncode != 0:
                state[request_uuid]["log"] += f"img2simg returned {p.return_code}\n"
                state[request_uuid]["error"] = True
                shutil.rmtree(gsi_dir)
                await asyncio.sleep(3)
                return

            state[request_uuid]["log"] += f"Deleting unsparsed GSI\n"
            os.remove(f"{gsi_dir}/{gsi_file}.raw")
    else:
        state[request_uuid]["log"] += f"Unsupported format?\n"
        state[request_uuid]["error"] = True
        shutil.rmtree(gsi_dir)
        await asyncio.sleep(3)
        return

    shutil.move(f"{gsi_dir}/{gsi_file}", f"{gsi_dir}/template/system.img")

    state[request_uuid]["log"] += f"Unsparsing the GSI\n"
    p = await async_Popen(loop, ["./simg/simg2img", f"{gsi_dir}/template/system.img", f"{gsi_dir}/template/system.img.raw"])
    await async_communicate(loop, p)

    if p.returncode != 0:
        state[request_uuid]["log"] += f"simg2img returned {p.returncode}\n"
        state[request_uuid]["error"] = True
        shutil.rmtree(gsi_dir)
        await asyncio.sleep(3)
        return

    raw_size = os.path.getsize(f"{gsi_dir}/template/system.img.raw")
    state[request_uuid]["log"] += f"Raw size of the GSI is {raw_size}\n"

    state[request_uuid]["log"] += f"Deleting unsparsed GSI\n"
    os.remove(f"{gsi_dir}/template/system.img.raw")

    state[request_uuid]["log"] += f"Replacing the template values\n"
    with open(f"{gsi_dir}/template/dynamic_partitions_op_list", "r") as f:
        data = f.read()
        data = data.replace("[raw_size]", str(raw_size))

    with open(f"{gsi_dir}/template/dynamic_partitions_op_list", "w") as f:
        f.write(data)

    with open(f"{gsi_dir}/template/META-INF/com/google/android/updater-script", "r") as f:
        data = f.read()
        data = data.replace("[gsi_file]", gsi_file)

    with open(f"{gsi_dir}/template/META-INF/com/google/android/updater-script", "w") as f:
        f.write(data)

    state[request_uuid]["log"] += f"Converting GSI to system.new.dat\n"
    p = await async_Popen(loop, ["python3", "img2sdat/img2sdat.py", "-v", "4", "-o", f"{gsi_dir}/template", f"{gsi_dir}/template/system.img"])
    await async_communicate(loop, p)

    if p.returncode != 0:
        state[request_uuid]["log"] += f"img2sdat returned {p.returncode}\n"
        state[request_uuid]["error"] = True
        shutil.rmtree(gsi_dir)
        await asyncio.sleep(3)
        return

    state[request_uuid]["log"] += f"Deleting sparsed GSI\n"
    os.remove(f"{gsi_dir}/template/system.img")

    state[request_uuid]["log"] += f"Compressing system.new.dat with Brotli (might take a while)\n"
    p = await async_Popen(loop, ["brotli", "-j1", f"{gsi_dir}/template/system.new.dat"])
    await async_communicate(loop, p)

    if p.returncode != 0:
        state[request_uuid]["log"] += f"brotli returned {p.returncode}\n"
        state[request_uuid]["error"] = True
        shutil.rmtree(gsi_dir)
        await asyncio.sleep(3)
        return

    # TODO: Do something about this hack
    state[request_uuid]["log"] += f"Creating a ZIP archive (might take a while)\n"
    ret = await async_call(loop, f"cd {gsi_dir}/template && zip -r0 ../{gsi_file.replace('.img', '.zip')} *")

    if ret != 0:
        state[request_uuid]["log"] += f"zip returned {p.returncode}\n"
        state[request_uuid]["error"] = True
        shutil.rmtree(gsi_dir)
        await asyncio.sleep(3)
        return

    state[request_uuid]["log"] += f"Finished request {request_uuid}\n"
    state[request_uuid]["log"] += "Link will be expired after 15 minutes\n"

    state[request_uuid]["finished"] = True
    state[request_uuid]["downloaded"] = False
    state[request_uuid]["download_from"] = f"{gsi_dir}/{gsi_file.replace('.img', '.zip')}"
    state[request_uuid]["zip_name"] = gsi_file.replace('.img', '.zip')

    shutil.rmtree(f"{gsi_dir}/template")

    for x in range(0, 900):
        if state[request_uuid]["downloaded"]:
            break

        await asyncio.sleep(1)

    shutil.rmtree(gsi_dir)
    del state[request_uuid]

@routes.post("/upload")
async def upload(req):
    request_uuid = str(uuid.uuid4())
    gsi_dir = tempfile.mkdtemp()
    gsi_file = None
    gsi_format = None
    gsi_arch = None

    async for field in (await req.multipart()):
        if field.name == "gsi":
            if not field.filename:
                shutil.rmtree(gsi_dir)
                return web.Response(text="Cannot determine the filename of the file", headers=cors)

            gsi_file = field.filename

            with open(f"{gsi_dir}/{field.filename}", "wb") as f:
                while True:
                    chunk = await field.read_chunk()
                    if not chunk:
                        break

                    f.write(chunk)
        elif field.name == "format":
            gsi_format = (await field.read()).decode("UTF-8")
        elif field.name == "arch":
            gsi_arch = (await field.read()).decode("UTF-8")

    if not gsi_format:
        shutil.rmtree(gsi_dir)
        return web.Response(text="Format field is empty", headers=cors)

    if not gsi_arch:
        shutil.rmtree(gsi_dir)
        return web.Response(text="Arch field is empty", headers=cors)

    if gsi_arch not in ["arm64"]:
        shutil.rmtree(gsi_dir)
        return web.Response(text="Unsupported arch", headers=cors)

    asyncio.create_task(process_gsi(gsi_dir, gsi_file, gsi_format, gsi_arch, request_uuid))

    return web.Response(text=request_uuid, headers=cors)

@routes.get("/download")
async def download(req):
    request_uuid = req.query.get("id")

    if not request_uuid:
        return web.Response(text="ID is not valid", headers=cors)

    status = state.get(request_uuid)

    if not status:
        return web.Response(text="ID is not valid", headers=cors)

    res = web.StreamResponse()
    res.headers["Content-Type"] = "application/octet-stream"
    res.headers["Content-Length"] = str(os.path.getsize(status["download_from"]))
    res.headers["Content-Disposition"] = f"attachment; filename=\"{status['zip_name']}\""

    await res.prepare(req)

    with open(status["download_from"], "rb") as f:
        while chunk := f.read(4096):
            await res.write(chunk)

    await asyncio.sleep(3)

    state[request_uuid]["downloaded"] = True

@routes.post("/identify")
async def identify(req):
    loop = asyncio.get_running_loop()
    temp_dir = tempfile.mkdtemp()

    async for field in (await req.multipart()):
        if field.name == "file":
            size = 0

            if not field.filename:
                return web.Response(text="Cannot determine the filename of the file", headers=cors)

            with open(f"{temp_dir}/{field.filename}", "wb") as f:
                while True:
                    if size > 65535:
                        return web.Response(text="The file is longer than 64 KB", headers=cors)

                    chunk = await field.read_chunk()
                    if not chunk:
                        break

                    size += len(chunk)
                    f.write(chunk)

    p = await async_Popen(loop, ["file", f"{temp_dir}/{field.filename}"])
    stdout, stderr = await async_communicate(loop, p)
    stdout = stdout.decode()

    shutil.rmtree(temp_dir)

    return web.Response(text=stdout, headers=cors)

@routes.get("/progress")
async def progress(req):
    request_uuid = req.query.get("id")

    if not request_uuid:
        return web.json_response({}, headers=cors)

    status = state.get(request_uuid)

    if not status:
        return web.json_response({}, headers=cors)

    return web.json_response(status, headers=cors)

@routes.get("/")
async def index(req):
    return web.Response(body=index_html, content_type="text/html")

@routes.route("OPTIONS", "/{tail:.*}")
async def cors_options(req):
    return web.Response(headers=cors)

async def chmod_hack():
    loop = asyncio.get_running_loop()
    await async_call(loop, "chmod 755 simg/simg2img")
    await async_call(loop, "chmod 755 simg/img2simg")

asyncio.run(chmod_hack())
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
app = web.Application()
app.add_routes(routes)
web.run_app(app, port=os.environ.get("PORT", 8080))
