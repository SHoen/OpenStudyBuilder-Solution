
function generateDownload (blobData, fileName) {
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blobData)
  link.download = fileName
  link.click()
  URL.revokeObjectURL(link.href)
}

export default {
  generateDownload
}
