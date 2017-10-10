<!DOCTYPE html>
<html>
    <head>
    </head>
    <!-- frameset is deprecated in html5, but it still works. -->
    <frameset framespacing="0" framepadding="0" cols="50%,50%" frameborder="1" nore3size="noresize" style="padding: 0px; margin: 0px">
        <frame name="navigator_left_frame" src="/navigator/?${request.query_string | n}" style="padding: 0px; margin: 0px"></frame>
        <frame name="navigator_right_frame" style="padding: 0px; margin: 0px"></frame>
    </frameset>
</html>
