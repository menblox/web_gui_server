import asyncio

async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    
    return {
        "result": (f'[stdout]\n{stdout.decode("cp866")}') if stdout else "",    #cp866 для Windows, на Linux по умолчанию utf-8
        "error": (f'[stderr]\n{stderr.decode("cp866")}') if stderr else "",
        "returncode": proc.returncode
    }