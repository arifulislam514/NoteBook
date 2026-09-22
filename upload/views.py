import cloudinary
import cloudinary.uploader
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from common.response import success_response, error_response

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class ImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if 'image' not in request.FILES:
            return error_response("No image provided", status=400)

        image_file = request.FILES['image']

        if image_file.size > MAX_FILE_SIZE:
            return error_response("File too large. Max 10MB", status=400)

        filename = image_file.name
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            return error_response("Invalid file type", status=400)

        try:
            upload_result = cloudinary.uploader.upload(
                image_file,
                resource_type='image'
            )
            url = upload_result.get('secure_url') or upload_result.get('url')
            return success_response({"url": url}, status=200)
        except Exception as e:
            return error_response(f"Upload failed: {str(e)}", status=400)
