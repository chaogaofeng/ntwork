# -*- coding: utf-8 -*-
import ntwork
import requests
from typing import Dict, Union

from oss import upload_file
from ntwork.utils.singleton import Singleton
from utils import generate_guid
from exception import ClientNotExists


class ClientWeWork(ntwork.WeWork):
    guid: str = ""


class ClientManager(metaclass=Singleton):
    __client_map: Dict[str, ntwork.WeWork] = {}
    callback_url: str = "http://sg.gushengai.com/prod-api/wechat/callback/msg"

    def new_guid(self):
        """
        生成新的guid
        """
        while True:
            guid = generate_guid("wework")
            if guid not in self.__client_map:
                return guid

    def create_client(self, guid=None):
        if not guid:
            guid = self.new_guid()
        wework = ClientWeWork()
        wework.guid = guid
        self.__client_map[guid] = wework

        # 注册回调
        wework.on(ntwork.MT_ALL, self.__on_callback)
        wework.on(ntwork.MT_RECV_WEWORK_QUIT_MSG, self.__on_quit_callback)
        return guid

    def get_client(self, guid: str) -> Union[None, ntwork.WeWork]:
        client = self.__client_map.get(guid, None)
        if client is None:
            raise ClientNotExists(guid)
        return client

    def remove_client(self, guid):
        if guid in self.__client_map:
            pid = self.__client_map[guid].pid
            del self.__client_map[guid]
            import os, signal
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                os.kill(pid, signal.SIGKILL)

    def __on_callback(self, wework, message):
        print(f"============= uid: {wework.guid}, recv msg: {message}", flush=True)
        if not self.callback_url:
            return
        client_message = {
            "guid": wework.guid,
            "message": message
        }
        if message.type in [ntwork.MT_RECV_IMAGE_MSG, ntwork.MT_RECV_VIDEO_MSG, ntwork.MT_RECV_VOICE_MSG,
                            ntwork.MT_RECV_FILE_MSG]:
            import os
            current_dir = os.getcwd()

            data = message["data"]
            aes_key = data["cdn"]["aes_key"]
            file_size = data["cdn"]["size"]

            if "url" in data["cdn"].keys() and "auth_key" in data["cdn"].keys():
                url = data["cdn"]["url"]
                auth_key = data["cdn"]["auth_key"]
                import hashlib
                md5_hash = hashlib.md5()
                md5_hash.update(url)
                file_id = md5_hash.hexdigest()
                save_path = os.path.join(current_dir, "tmp", file_id)
                result = wework.wx_cdn_download(url, auth_key, file_size, save_path)
                print(f"donload complete. {result}", flush=True)
                upload_file(save_path, file_id)
            elif "file_id" in data["cdn"].keys():
                file_id = data["cdn"]["file_id"]
                save_path = os.path.join(current_dir, "tmp", file_id)
                if message.type == ntwork.MT_RECV_IMAGE_MSG:
                    file_type = 2
                elif message.type == ntwork.MT_RECV_VIDEO_MSG:
                    file_type = 5
                elif message.type == ntwork.MT_RECV_VOICE_MSG:
                    file_type = 5
                elif message.type == ntwork.MT_RECV_FILE_MSG:
                    file_type = 5
                result = wework.c2c_cdn_download(file_id, aes_key, file_size, file_type, save_path)
                print(f"donload complete. {result}", flush=True)
                upload_file(save_path, file_id)
            else:
                print(f"something is wrong, data: {data}", flush=True)

        resp = requests.post(self.callback_url, json=client_message)
        print(f"============= callback: {self.callback_url}, resp: {resp}", flush=True)

    def __on_quit_callback(self, wework):
        print(f"============= uid: {wework.guid} quit", flush=True)
        self.__on_callback(wework, {"type": ntwork.MT_RECV_WEWORK_QUIT_MSG, "data": {}})
        self.remove_client(wework.guid)
