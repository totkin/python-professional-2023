import sys

print(sys.version_info > (3,))
print(type(sys.version_info.major))

error_messages = {
    'def0': "b",
    'def3': "s"
}
error_messages.update({
    'def1': "Value 1",
    'def0': "Value 0",
    'def2': "Length 2"
})
print(error_messages)
