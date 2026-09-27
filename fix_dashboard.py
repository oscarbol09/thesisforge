
with open("gui/js/dashboard.js", encoding="utf-8") as f:
    content = f.read()

target = r"""@click="confirmDeleteProject('${safeId}', '${safeTitle.replace(/'/g, "\\'")}')\""""
replacement = r"""@click="confirmDeleteProject('${safeId}')\""""

content = content.replace(target, replacement)

with open("gui/js/dashboard.js", "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
