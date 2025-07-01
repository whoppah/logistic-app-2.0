from backend.logistics.processing.utils import check_delta_in_dataframe


class InvoiceProcessor:
    def __init__(self, slack_service):
        self.slack = slack_service

    def process_messages(self, df_list):
        messages = self.slack.get_latest_messages()
        reaction_dict = {}

        for msg in messages:
            ts = msg.get("ts")
            text = msg.get("text", "")
            reactions = msg.get("reactions", [])
            partner = self.slack.extract_partner(text)
            file_name_pdf = ""

            if ts and not reactions and "files" in msg and partner:
                for file in msg["files"]:
                    file_id = file["id"]
                    file_name = file["name"]

                    if file_name.endswith(".pdf") and partner == "libero_logistics":
                        file_name_pdf = self.slack.download_file(file_id)
                    elif file_name.endswith(".xlsx") or (file_name.endswith(".pdf") and partner in ["brenger", "transpoksi", "wuunder"]):
                        redis_key = self.slack.download_file(file_id)

                        if redis_key:
                            condition_met, flag = check_delta_in_dataframe(
                                redis_key=redis_key,
                                redis_key_pdf="",
                                file_name=redis_key,
                                file_name_pdf=file_name_pdf,
                                partner_value=partner,
                                df_list=df_list
                            )
                            if condition_met and flag:
                                self.slack.react_to_message(ts, "white_check_mark")
                                reaction_dict[ts] = "white_check_mark"
                            elif flag:
                                self.slack.react_to_message(ts, "large_red_square")
                                reaction_dict[ts] = "large_red_square"
        return reaction_dict

    def clear_reactions(self, reaction_dict):
        for ts, emoji in reaction_dict.items():
            self.slack.remove_reaction(ts, emoji)
