import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime


def current_milli_time():
    return int(round(time.time() * 1000))


# Too complicated -> recocomend splitting out into something like validate_thread
# def is_thread_valid():
#     check thread validity
#     return True/False

# def singlePath():
#     if not is_thread_valid:
#         return 0
#     rest of method body...


def singlePath(root, thread):

    ################################################################################
    # Validation section
    ################################################################################

    # It looks like you're assuming a pretty complex nested dictionary structure - maybe throw some asserts in? Could help with debugging

    participant = thread["conversation"]["conversation"]["participant_data"]

    if "phone_number" in participant[0].keys():
        # rename to phone_number?
        phone = participant[0]["phone_number"]["e164"]
        if "i18n_data" in participant[0]["phone_number"].keys():
            is_valid = participant[0]["phone_number"]["i18n_data"]["is_valid"]
            if not is_valid:
                # Skip short code phone numbers
                return 0
            # name
            name = participant[0]["fallback_name"]
        else:
            return 0
    # Unknown case where object 0 has no phone number and is the only object in array. Submitted by reddit user.
    elif len(thread["conversation"]["conversation"]["participant_data"]) < 2:
        return 0
    # if this fails and it's not a Group message, then it's a hangouts message (or incoming message?)
    elif "phone_number" in participant[1].keys():
        phone = participant[1]["phone_number"]["e164"]
        name = participant[1]["fallback_name"]
        if "i18n_data" in participant[1]["phone_number"].keys():
            is_valid = participant[1]["phone_number"]["i18n_data"]["is_valid"]
            if not is_valid:
                # Skip short code phone numbers
                return 0
        else:
            return 0
    # Ignoring native Hangouts message threads
    else:
        return 0

    ################################################################################
    # End validation section
    ################################################################################

    message_count = 0

    for msg in thread["events"]:
        try:
            message_count += 1
            # Inbound/Outbound
            # Overloading the type keyword seems dangerous -> refactor to msg_type
            type = getType(msg)

            # Content of the message
            text = getMessage(msg)

            # refactor to
            # has_attachment = text is None
            # if has_attachment: continue

            if text is None:
                continue

            # Time of the message
            ts = getTimestamp(msg)

            if type == 1:
                # 1 = Received
                datesent = ts
            else:
                # 2 = Sent
                datesent = 0

            # Convert timestamp into date
            date = getReadableDate(ts)

            ET.SubElement(
                root,
                "sms",
                protocol="0",
                address=str(phone),
                date=str(ts),
                type=str(type),
                subject="null",
                body=str(text),
                toa="null",
                sc_toa="null",
                service_center="null",
                read="1",
                status="-1",
                locked="0",
                date_sent=str(datesent),
                sub_id="-1",
                readable_date=str(date),
                contact_name=str(name),
            )
        # A bit confused as to why this is here
        except Exception:
            print(msg)
            raise

    return message_count


def groupPath(root, thread):
    user_ids = groupIDs(thread)

    if user_ids is None:
        return 0

    message_count = buildGroupConvo(root, thread, user_ids)

    return message_count


def groupIDs(thread):
    user_ids = {}

    phone_found = False
    for participant in thread["conversation"]["conversation"][
        "participant_data"
    ]:  # deeply nested dict structure freaks me out a bit again. Would throw in some asserts/helper functions to extract data modularly (if the JSON structure changes in the future)
        try:
            userID = participant["id"]["chat_id"]
            if participant.get("phone_number"):
                phone_found = True
                phoneNumber = participant["phone_number"]["e164"]
                userName = participant["fallback_name"]
                user_ids[userID] = (userName, phoneNumber)
            else:
                # if this is an mms thread, the owner's phone # will be in "fallback_name" for some reason
                # so, if we find other numbers, and only one is missing, it should be your own number
                fallback = participant.get("fallback_name")
                if fallback:
                    user_ids[userID] = (fallback, fallback)
        except Exception:
            print(participant)
            raise

    if phone_found:
        return user_ids
    else:
        # Ignoring native Hangouts message threads
        return None


def buildGroupConvo(root, thread, user_ids):
    message_count = 0

    for msg in thread["events"]:
        try:
            message_count += 1

            # Sender of the message
            sender_id = msg["sender_id"]["chat_id"]

            # Determine message type
            type = getType(msg)

            # Content of the message
            text = getMessage(msg)

            # has attachment
            if text is None:
                continue

            # Time of the message
            ts = getTimestamp(msg)

            if type == 1:
                # Received
                datesent = ts
            else:
                # Sent
                # 0 seems like a magic number, maybe set to None, or a globakl UNKNOWN_DATE var?
                datesent = 0

            date = getReadableDate(ts)

            xml_address = "~".join([user[1] for user in user_ids.values()])
            xml_name = ", ".join([user[0] for user in user_ids.values()])

            mms_root = ET.SubElement(
                root,
                "mms",
                address=str(xml_address),
                date=str(ts),
                read="1",
                date_sent=str(datesent),
                sub_id="-1",
                readable_date=str(date),
                contact_name=str(xml_name),
                rr="129",
                ct_t="application/vnd.wap.multipart.related",  # should put magic string in a var and document
                seen="1",
                text_only="1",
                msg_box=str(type),  # SMS type
            )

            if type == 1:
                # Received
                mms_root.set("m_type", "132")
            else:
                # Sent
                mms_root.set("m_type", "128")
                # PduHeaders.RESPONSE_STATUS_OK (0x80)
                # Put a link to documentation of these codes
                mms_root.set("resp_st", "128")

            parts = ET.SubElement(mms_root, "parts")
            ET.SubElement(parts, "part", seq="0", ct="text/plain", text=text)

            addrs = ET.SubElement(mms_root, "addrs")
            for key, (name, phone) in user_ids.items():
                # MMS uses PDUHeaders as type
                if key == sender_id:
                    # PduHeaders.FROM (0x89)
                    type = "137"
                else:
                    # PduHeaders.TO (0x97)
                    type = "151"
                ET.SubElement(
                    addrs, "addr", address=phone, type=type, charset="106"
                )

        except Exception:
            print(msg)
            raise

    return message_count


# Assuming all messages are 1 = Received or 2 = Sent
# Ignoring: 3 = Draft, 4 = Outbox, 5 = Failed, 6 = Queued
# Switch to using an enum rather than magic numbers https://docs.python.org/3/library/enum.html
def getType(msg):
    senderID = msg["sender_id"]["gaia_id"]
    userID = msg["self_event_state"]["user_id"]["gaia_id"]

    if senderID == userID:
        # Sent
        return 2
    else:
        # Recieved
        return 1


def getMessage(msg):
    # Ensure that msg contians 'chat_message'
    if "chat_message" not in msg:
        return None

    message_content = msg["chat_message"]["message_content"]

    # Check message for attachments
    text = ""
    if "attachment" in message_content:
        for attachment in message_content["attachment"]:
            types = attachment["embed_item"]["type"]
            for type in types:
                if (
                    type == "PLUS_PHOTO"
                ):  # Use Enums here as well MessageType.PLUS_PHOTO
                    url = attachment["embed_item"]["plus_photo"]["url"]
                    # Strip unnecessary spaces
                    url = re.sub(r"\s+", "", url)
                    text += url + "\n"
                elif type == "PLUS_AUDIO_V2":
                    # Voicemail audio, not easily referencable as link
                    # Setting an informational header instead
                    text += "Voicemail transcript:\n"
                elif type == "THING_V2":
                    url = attachment["embed_item"]["thing_v2"]["url"]
                    # Strip unnecessary spaces
                    url = re.sub(r"\s+", "", url)

                    name = attachment["embed_item"]["thing_v2"].get("name")
                    text += name if name else "Attachment" + "\n" + url
                # THING and PLACE_V2 are never the sole attachment type
                elif type in ("THING", "PLACE_V2"):
                    continue
                else:
                    raise Exception(f"Unknown attachment type: {type}")

    if message_content.get("segment"):
        segments = message_content["segment"]
        for segment in segments:
            type = segment["type"]
            if type == "TEXT":
                text += segment["text"]
            elif type == "LINE_BREAK":
                text += "\n"
            elif type == "LINK":
                url = segment["text"]
                # Strip unnecessary spaces
                url = re.sub(r"\s+", "", url)
                text += url

    if not text:
        raise Exception(f"No text found for message {msg}")

    return text


# document units
def getTimestamp(msg):
    ts = int(int(msg["timestamp"]) / 1000)

    return ts


def getReadableDate(ts):
    date = (
        datetime.fromtimestamp(int(int(ts) / 1000))
        .strftime("%b %d, %Y %I:%M:%S %p")
        .replace(" 0", " ")
    )

    return date


def main():
    os.chdir(sys.path[0])
    # assert this file exists and looks like you expect
    # use https://docs.python.org/3/library/argparse.html to pass file as cmd line parameter?
    with open("Hangouts.json", encoding="utf8") as f:
        datastore = f.read()

    data = json.loads(datastore)

    root = ET.Element(
        "smses",
        message_count=str(0),
        backup_set="145bea68-a1f4-4068-a631-06757067e675",  # Magic string should be in a variable and documented
        backup_date=str(current_milli_time()),
    )

    message_count = 0
    for thread in data["conversations"]:
        # Group message check
        if len(thread["conversation"]["conversation"]["participant_data"]) > 2:
            message_count += groupPath(root, thread)
        else:
            message_count += singlePath(root, thread)

    root.set("count", str(message_count))
    tree = ET.ElementTree(root)
    # use argparse to pass outfile as cmd line parameter?
    tree.write("Hangouts.xml")


main()
