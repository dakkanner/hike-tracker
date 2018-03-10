import os
import sqlite3
import ftplib

# `pip3 install pillow`
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# `pip3 install python-resize-image`
from resizeimage import resizeimage

# `pip3 install mysqlclient`
import MySQLdb


def Run():
    pwd = os.getcwd()
    print('Current directory is: ' + pwd)
    
    files_list = os.listdir('.')
    print ('Number of files found ' + str(len(files_list)))
    
    if not os.path.exists('done'):
        os.makedirs('done')
    
    extensions = ['jpg', 'JPG','png', 'PNG','gif', 'GIF']
    
    locations_not_found = []
    
    totalLen = len(os.listdir('.'))
    currentCount = 0
    
    for new_photo_filename in os.listdir('.'):
        currentCount = currentCount + 1
        print ('Image ' + str(currentCount) + '/' + str(totalLen) + ": " + new_photo_filename)
        
        if not any(extension in new_photo_filename for extension in extensions):
            print('Rejecting because not recognised photo format ' + new_photo_filename)
            continue
        if 'thumbnail' in new_photo_filename:
            print('Rejecting because it is already a thumbnail: ' + new_photo_filename)
            continue
        
        
        print('Connecting to MySQL')
        mysql_connection = MySQLdb.connect(ARGS GO HERE)
        print('    Connected to MySQL')
        mysql_connection_cursor = mysql_connection.cursor()
        
        select_photo = "SELECT * FROM hikepoints WHERE pointfilename=%s LIMIT 1"
        mysql_connection_cursor.execute(select_photo, [new_photo_filename])
        
        if mysql_connection_cursor.rowcount > 0:
            print('Photo already in SQL: ' + new_photo_filename)
            mysql_connection_cursor.close()
            mysql_connection.close()
            continue
        
        
        print('Finding data for photo: ' + new_photo_filename)
        meta_data = ImageMetaData(new_photo_filename)
        latlng = meta_data.get_lat_lng()
        if not latlng[0]:
            locations_not_found.append(new_photo_filename)
            print('    Photo location not found: ' + new_photo_filename)
            mysql_connection_cursor.close()
            mysql_connection.close()
            continue
            
        print('    Photo lat: ' + str(latlng[0]))
        print('    Photo lon: ' + str(latlng[1]))
        exif_data = meta_data.get_exif_data()
        if 'DateTimeOriginal' in exif_data:
            print('    Photo datetime: ' + str(exif_data['DateTimeOriginal']))
        
        thumbnail_filename = 'thumbnail_' + new_photo_filename
        image_file = Image.open(new_photo_filename)
        
        image_file.size
        print('    Photo width: ' + str(image_file.size[0]))
        print('    Photo height: ' + str(image_file.size[1]))
        new_sizes = NewDimensions(image_file.size[0], image_file.size[1])
        print('    New width: ' + str(new_sizes[0]))
        print('    New height: ' + str(new_sizes[1]))
        
        resized_image_file = image_file.resize(new_sizes, Image.ANTIALIAS)
        if 'Orientation' in exif_data:
            orientation = exif_data['Orientation']
            if orientation in [3, 4]:
                resized_image_file = resized_image_file.rotate(180, expand=True)
                print('      Rotated 180 degrees')
            if orientation in [5, 6]:
                resized_image_file = resized_image_file.rotate(270, expand=True)
                print('      Rotated 270 degrees')
            if orientation in [7, 8]:
                resized_image_file = resized_image_file.rotate(90, expand=True)
                print('      Rotated 90 degrees')
        resized_image_file.save(thumbnail_filename)
        print('  Thumbnail saved!')
        
        
        print('  Connecting to FTP server')
        ftp_session = ftplib.FTP('ftp.paradoxtrail.net','fileuploader@paradoxtrail.net','33&HMBRgRUDpF2up')
        ftp_session.cwd('./gpx/photos/')
        print('      Uploading original')
        file = open(new_photo_filename,'rb')                        # file to send
        ftp_session.storbinary('STOR ' + new_photo_filename, file)  # send the file
        file.close()                                                # close file and FTP
        print('      Uploading thumbnail')
        ftp_session.cwd('../thumbnails/')
        file = open(thumbnail_filename,'rb')                        # file to send
        ftp_session.storbinary('STOR ' + thumbnail_filename, file)  # send the file
        file.close()
        ftp_session.quit()
        print('  Done uploading to FTP server')
        
        
        print('  Inserting entry into SQL')
        add_photo = ("INSERT INTO hikepoints " 
                "(pointfilename, pointtitle, pointlat, pointlon, pointtype) " 
                "VALUES (%s, %s, %s, %s, 'photo')")
        
        title = new_photo_filename
        if 'DateTimeOriginal' in exif_data:
            title = str(exif_data['DateTimeOriginal'])
        
        data_photo = (new_photo_filename, title, str(latlng[0]), str(latlng[1]))
        
        print('    Inserting ' + new_photo_filename)
        mysql_connection_cursor.execute(add_photo, data_photo)
        print('    Added photo data into table, row #' + str(mysql_connection_cursor.lastrowid))
        mysql_connection.commit()
        
        mysql_connection_cursor.close()
        mysql_connection.close()
        
        
        print('    Moving photo to "done" folder')
        os.rename('./' + new_photo_filename, './done/' + new_photo_filename)
        
        try:
            os.remove(thumbnail_filename)
            print('    Removed thumbnail')
        except OSError:
            pass
        
        print('  Photo done: ' + new_photo_filename)
    
    if len(locations_not_found) > 0:
        print('\n\nPhoto locations not found for')
        for photo_filename in locations_not_found:
            print('    ' + photo_filename)
    else: 
        print('\n\nAll photos had locations')
        
        
def NewDimensions(width, height):
    max_width = 1000
    max_height = 800
    target_width = 500
    target_height = 500
    min_width = 150
    min_height = 150
    
    ratio = width / height
    inverse_ratio = height / width
    
    new_width = 0
    new_height = 0
    if ratio > 1:
        new_width = target_width
        new_height = inverse_ratio * target_width
        if new_height < min_height:
            new_width = max_width
            new_height = inverse_ratio * max_width
    else:
        new_width = ratio * target_height
        new_height = target_height
        if new_width < min_width:
            new_width = ratio * max_height
            new_height = max_height
    
    return round(new_width), round(new_height)
    
    
class ImageMetaData(object):
    '''
    Blatantly copy/pasted from https://www.codingforentrepreneurs.com/blog/extract-gps-exif-images-python/
    Extract the exif data from any image. Data includes GPS coordinates, 
    Focal Length, Manufacture, and more.
    '''
    exif_data = None
    image = None

    def __init__(self, img_path):
        self.image = Image.open(img_path)
        #print(self.image._getexif())
        self.get_exif_data()
        super(ImageMetaData, self).__init__()

    def get_exif_data(self):
        """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
        exif_data = {}
        info = self.image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]

                    exif_data[decoded] = gps_data
                else:
                    #print(decoded + ': ' + str(value))
                    exif_data[decoded] = value
        self.exif_data = exif_data
        return exif_data

    def get_if_exist(self, data, key):
        if key in data:
            return data[key]
        return None

    def convert_to_degress(self, value):

        """Helper function to convert the GPS coordinates 
        stored in the EXIF to degress in float format"""
        d0 = value[0][0]
        d1 = value[0][1]
        d = float(d0) / float(d1)

        m0 = value[1][0]
        m1 = value[1][1]
        m = float(m0) / float(m1)

        s0 = value[2][0]
        s1 = value[2][1]
        s = float(s0) / float(s1)

        return d + (m / 60.0) + (s / 3600.0)

    def get_lat_lng(self):
        """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
        lat = None
        lng = None
        exif_data = self.get_exif_data()
        #print(exif_data)
        if "GPSInfo" in exif_data:      
            gps_info = exif_data["GPSInfo"]
            gps_latitude = self.get_if_exist(gps_info, "GPSLatitude")
            gps_latitude_ref = self.get_if_exist(gps_info, 'GPSLatitudeRef')
            gps_longitude = self.get_if_exist(gps_info, 'GPSLongitude')
            gps_longitude_ref = self.get_if_exist(gps_info, 'GPSLongitudeRef')
            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                lat = self.convert_to_degress(gps_latitude)
                if gps_latitude_ref != "N":                     
                    lat = 0 - lat
                lng = self.convert_to_degress(gps_longitude)
                if gps_longitude_ref != "E":
                    lng = 0 - lng
        return lat, lng
    
Run()