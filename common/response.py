from rest_framework.response import Response


def success_response(data, status=200):
    if isinstance(data, list):
        return Response({"success": True, "data": data, "count": len(data)}, status=status)
    return Response({"success": True, "data": data}, status=status)


def error_response(message, status=400):
    return Response({"success": False, "error": message}, status=status)
