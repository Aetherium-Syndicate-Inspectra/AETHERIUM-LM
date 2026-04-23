1. *Modify `ChatMessage` class in `main.py`*
   - Update the constructor to accept an optional `image_src` parameter.
   - If `image_src` is provided, add an `ft.Image` control to the message's column.
2. *Update UI and state in `main` function*
   - Add a variable `selected_image_path` to track the attached image.
   - Add an `ft.Image` preview control (initially hidden) to the layout above the text field.
   - Update `handle_file_picker_result` to store the path and show the preview instead of immediately sending a message.
3. *Refactor `send_message_click`*
   - Update it to include the `selected_image_path` when creating the user's `ChatMessage`.
   - Clear the `selected_image_path` and hide the preview after sending.
   - Update the bot response to acknowledge the image.
4. *Complete pre commit steps*
   - Complete pre commit steps to make sure proper testing, verifications, reviews and reflections are done.
5. *Submit the change.*
   - Submit the enhanced chat application with image support.
